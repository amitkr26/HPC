# Zone 3 inference runtime — llama.cpp pinned build (PHASE3_INTEGRATION_BLUEPRINT.md P3.2)
# Built in CI (with internet); the running container has NO egress — S2 is
# enforced at the VM firewall/network level, noted in compose.yml.

FROM ubuntu:24.04 AS build
ARG LLAMA_REF=d854d98bae598388ecea1ed84396587e5edc326d
RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential cmake git libgomp1 && rm -rf /var/lib/apt/lists/*
WORKDIR /src
RUN git clone --depth 1 https://github.com/ggml-org/llama.cpp && \
    cd llama.cpp && git fetch --depth 1 origin ${LLAMA_REF} && git checkout FETCH_HEAD
# Same posture as the P2.5 cluster build (errata 17.1/17.2): Release, no
# tests/examples, server ON, quantize ON, curl OFF. GGML defaults to native
# for the build host — build the image ON the target class before deploying.
RUN cmake -S llama.cpp -B llama.cpp/build -DCMAKE_BUILD_TYPE=Release \
      -DLLAMA_BUILD_TESTS=OFF -DLLAMA_BUILD_EXAMPLES=OFF -DLLAMA_BUILD_APP=OFF \
      -DLLAMA_BUILD_TOOLS=ON -DLLAMA_BUILD_COMMON=ON -DLLAMA_USE_PREBUILT_UI=OFF \
      -DGGML_CURL=OFF -DLLAMA_CURL=OFF && \
    cmake --build llama.cpp/build -j"$(nproc)" --target llama-server llama-quantize

FROM ubuntu:24.04
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 \
      && rm -rf /var/lib/apt/lists/*
COPY --from=build /src/llama.cpp/build/bin/llama-server /usr/local/bin/llama-server
COPY --from=build /src/llama.cpp/build/bin/llama-quantize /usr/local/bin/llama-quantize
COPY boot_check.sh /usr/local/bin/boot_check.sh
RUN chmod +x /usr/local/bin/boot_check.sh
# Weights are mounted read-only at /models; digest provided via ZONE3_MODEL_MD5 (S8).
ENTRYPOINT ["/usr/local/bin/boot_check.sh"]
CMD ["llama-server", "-m", "/models/bdw-7b-sft-Q4_K_M.gguf", \
     "--host", "0.0.0.0", "--port", "8080", "-c", "4096"]
