# 1. Fetch HTML page
url = "https://www.berojgardegreewala.app/"
resp = requests.get(url, timeout=10, headers={
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
})
resp.raise_for_status()

# 2. Parse DOM tree with BeautifulSoup
soup = BeautifulSoup(resp.text, "html.parser")

# 3. Extract job titles and links
# We will scan for typical container structures or anchor tags containing jobs.
records = []

# Looking for anchor elements that typically represent post links/titles
for link in soup.find_all('a'):
    title_text = link.get_text(strip=True)
    href = link.get('href', '')

    # Filter elements that likely contain job postings based on keyword context or length
    if len(title_text) > 10 and any(keyword in title_text.lower() for keyword in ['job', 'vacancy', 'recruitment', 'bharti', 'post', 'railway', 'bank', 'police', 'ssc']):
        # Handle relative URLs
        full_url = href if href.startswith('http') else f"{url.rstrip('/')}/{href.lstrip('/')}"
        records.append({
            "Job Title": title_text,
            "Link": full_url
        })

# Also inspect heading elements as fallbacks
if not records:
    for heading in soup.find_all(['h1', 'h2', 'h3', 'h4']):
        title_text = heading.get_text(strip=True)
        parent_a = heading.find_parent('a')
        href = parent_a.get('href', '') if parent_a else ""
        full_url = href if (not href or href.startswith('http')) else f"{url.rstrip('/')}/{href.lstrip('/')}"
        if len(title_text) > 5:
            records.append({
                "Job Title": title_text,
                "Link": full_url
            })

# Save and Display
df_jobs = pd.DataFrame(records).drop_duplicates()
df_jobs.to_csv("job_posts.csv", index=False)
print(f"Found {len(df_jobs)} potential job posts:")
display(df_jobs.head(20))