// top1agree.cpp -- BDW Phase 2.5 (blueprint S8.3): teacher-forced top-1
// agreement between a GGUF model and an HF greedy trajectory.
//
// The HF side (transformers, merged bf16) generates each suite answer greedily
// and writes the FULL token id sequence (chat-prompt ids + answer ids).  For
// every answer position i we ask the GGUF model: what is your argmax token
// given ids[0..i-1]?  Agreement counts how often that argmax equals the bf16
// token ids[i] -- exactly the Phase-0 export_test.py top-1 metric, now
// bf16-merged vs Q4_K_M instead of fp32 vs int8.
//
// input : TSV  pid \t answer_start \t id id id ...   (answer_start = #prompt ids)
// output: TSV  pid \t agree \t total \t first_div
//         first_div = 0-based offset of the first disagreement inside the
//         answer, -1 when every position agrees, -2 malformed row,
//         -3 llama_decode failure.
//
// Build (appended target in the top-level CMakeLists.txt):
//   cmake --build build --target top1agree

#include "llama.h"

#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>

static void die(const char * msg) {
    std::fprintf(stderr, "top1agree: %s\n", msg);
    std::exit(1);
}

static void split_tsv(const std::string & line, std::vector<std::string> & f) {
    f.clear();
    std::string cur;
    for (char c : line) {
        if (c == '\t') {
            f.push_back(cur);
            cur.clear();
        } else {
            cur += c;
        }
    }
    f.push_back(cur);
}

int main(int argc, char ** argv) {
    std::string model_path;
    std::string in_path;
    std::string out_path;
    int n_threads = 4;
    int n_ctx     = 2048;

    for (int i = 1; i + 1 < argc; i += 2) {
        const std::string a = argv[i];
        if      (a == "--model")   model_path = argv[i + 1];
        else if (a == "--input")   in_path    = argv[i + 1];
        else if (a == "--output")  out_path   = argv[i + 1];
        else if (a == "--threads") n_threads  = std::atoi(argv[i + 1]);
        else if (a == "--ctx")     n_ctx      = std::atoi(argv[i + 1]);
        else                       die(("unknown arg " + a).c_str());
    }
    if (model_path.empty() || in_path.empty() || out_path.empty()) {
        die("usage: top1agree --model M.gguf --input in.tsv --output out.tsv "
            "[--threads N] [--ctx N]");
    }

    llama_backend_init();

    llama_model_params mparams = llama_model_default_params();
    mparams.n_gpu_layers = 0;   // CPU inference: agreement only, not latency
    llama_model * model = llama_model_load_from_file(model_path.c_str(), mparams);
    if (model == nullptr) {
        die("model load failed");
    }

    llama_context_params cparams = llama_context_default_params();
    cparams.n_ctx   = n_ctx;
    cparams.n_batch = n_ctx;
    llama_context * ctx = llama_init_from_model(model, cparams);
    if (ctx == nullptr) {
        die("context init failed");
    }
    llama_set_n_threads(ctx, n_threads, n_threads);

    const llama_vocab * vocab = llama_model_get_vocab(model);
    const int n_vocab = llama_vocab_n_tokens(vocab);

    std::ifstream in(in_path.c_str());
    if (!in) {
        die("cannot open input");
    }
    std::ofstream out(out_path.c_str());
    if (!out) {
        die("cannot open output");
    }

    std::string line;
    long long prompts = 0;
    long long positions = 0;
    long long agree_n = 0;
    long long identical = 0;

    while (std::getline(in, line)) {
        if (line.empty() || line[0] == '#') {
            continue;
        }
        std::vector<std::string> f;
        split_tsv(line, f);
        if (f.size() != 3) {
            continue;
        }
        const std::string & pid = f[0];
        const int64_t start = std::strtoll(f[1].c_str(), nullptr, 10);

        std::vector<llama_token> ids;
        {
            std::istringstream ss(f[2]);
            long long t;
            while (ss >> t) {
                ids.push_back(static_cast<llama_token>(t));
            }
        }
        const int n = static_cast<int>(ids.size());
        if (n < 2 || start < 1 || start >= n) {
            out << pid << "\t0\t0\t-2\n";
            continue;
        }

        llama_batch batch = llama_batch_init(n, 0, 1);
        batch.n_tokens = n;
        batch.embd     = nullptr;
        for (int i = 0; i < n; i++) {
            batch.token[i]     = ids[i];
            batch.pos[i]       = i;
            batch.n_seq_id[i]  = 1;
            batch.seq_id[i][0] = 0;
            batch.logits[i]    = 1;   // need every position's argmax
        }

        llama_memory_clear(llama_get_memory(ctx), true);
        const int rc = llama_decode(ctx, batch);
        if (rc != 0) {
            std::fprintf(stderr, "top1agree: decode failed pid=%s rc=%d\n",
                         pid.c_str(), rc);
            out << pid << "\t0\t0\t-3\n";
            llama_batch_free(batch);
            continue;
        }

        int agree  = 0;
        int first  = -1;
        for (int i = static_cast<int>(start) - 1; i <= n - 2; i++) {
            const float * row = llama_get_logits_ith(ctx, i);
            int   am   = 0;
            float best = row[0];
            for (int v = 1; v < n_vocab; v++) {
                if (row[v] > best) {
                    best = row[v];
                    am   = v;
                }
            }
            if (am == static_cast<int>(ids[i + 1])) {
                agree++;
            } else if (first < 0) {
                first = i - (static_cast<int>(start) - 1);
            }
        }
        const int total = n - static_cast<int>(start);
        out << pid << "\t" << agree << "\t" << total << "\t" << first << "\n";

        prompts    += 1;
        positions  += total;
        agree_n    += agree;
        if (first < 0) {
            identical += 1;
        }
        llama_batch_free(batch);
    }
    out.flush();

    std::printf("PROMPTS=%lld POSITIONS=%lld AGREE=%lld IDENTICAL=%lld RATE=%.6f\n",
                prompts, positions, agree_n, identical,
                positions > 0 ? static_cast<double>(agree_n) /
                                static_cast<double>(positions)
                              : 0.0);

    llama_free(ctx);
    llama_model_free(model);
    return 0;
}
