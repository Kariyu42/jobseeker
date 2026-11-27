"""Parsers run against small samples shaped like each board's real response."""
from fetcher.sources import arbeitnow, himalayas, hn, jobicy, remoteok, remotive, weworkremotely, workingnomads


def test_remoteok():
    data = [{"legal": "notice"}, {"id": "1", "slug": "s", "epoch": 1764000000, "company": "Acme",
            "position": "DevOps Engineer", "tags": ["devops", "aws"], "location": "Worldwide",
            "salary_min": 80000, "salary_max": 120000, "url": "https://remoteok.com/1", "description": "<p>k8s</p>"}]
    (j,) = remoteok.parse(data)
    assert j["title"] == "DevOps Engineer" and j["salary"] == "$80k–$120k" and j["location"] == "Worldwide"


def test_remotive():
    data = {"jobs": [{"id": 5, "url": "https://remotive.com/5", "title": "SRE", "company_name": "B",
                      "tags": ["k8s"], "job_type": "full_time", "publication_date": "2026-11-20T10:00:00",
                      "candidate_required_location": "Europe", "salary": "€60k", "description": "x"}]}
    (j,) = remotive.parse(data)
    assert j["location"] == "Europe" and j["posted_at"].startswith("2026-11-20")


def test_arbeitnow_only_remote():
    data = {"data": [
        {"slug": "a", "company_name": "C", "title": "DevOps", "remote": True, "url": "u", "tags": [], "job_types": ["full time"], "location": "Berlin", "created_at": 1764000000, "description": ""},
        {"slug": "b", "company_name": "C", "title": "DevOps", "remote": False, "url": "u", "tags": [], "job_types": [], "location": "Berlin", "created_at": 1764000000, "description": ""},
    ], "links": {"next": None}}
    (j,) = arbeitnow.parse(data)
    assert "berlin" in j["location"].lower()
    data["data"][0]["location"] = "Homeoffice"
    assert arbeitnow.parse(data)[0]["location"] == "Germany (Homeoffice)"


def test_himalayas():
    data = {"jobs": [{"title": "Platform Engineer", "companyName": "D", "applicationLink": "https://h/1", "guid": "https://h/1",
                      "pubDate": 1764000000, "locationRestrictions": ["Germany", "Spain"], "timezoneRestrictions": [1, 2],
                      "minSalary": 70000, "maxSalary": 90000, "currency": "EUR", "categories": ["DevOps"],
                      "seniority": "Mid-level", "employmentType": "Full Time", "description": "Terraform"}]}
    (j,) = himalayas.parse(data)
    assert j["location_list"] == ["Germany", "Spain"] and j["timezones"] == [1, 2] and j["salary"] == "€70k–€90k"
    assert himalayas.parse({"jobs": [{"title": "X", "companyName": "Y", "applicationLink": "z"}]})[0]["location"] == "Worldwide"


def test_jobicy():
    data = {"jobs": [{"id": 9, "url": "https://jobicy.com/9", "jobTitle": "DevOps Engineer", "companyName": "E",
                      "jobIndustry": ["DevOps & Sysadmin"], "jobType": ["full-time"], "jobGeo": "EMEA", "jobLevel": "Senior",
                      "jobDescription": "<p>AWS</p>", "pubDate": "2026-11-25 08:00:00",
                      "annualSalaryMin": "90000", "annualSalaryMax": "110000", "salaryCurrency": "USD"}]}
    (j,) = jobicy.parse(data)
    assert j["location"] == "EMEA" and j["salary"] == "$90k–$110k"


def test_wwr():
    xml = """<?xml version="1.0"?><rss><channel><item>
      <title>Acme: Senior DevOps Engineer</title><region>Anywhere in the World</region>
      <category>DevOps and Sysadmin</category><type>Full-Time</type>
      <description>&lt;p&gt;Kubernetes&lt;/p&gt;</description><pubDate>Tue, 25 Nov 2026 10:00:00 +0000</pubDate>
      <guid>https://weworkremotely.com/x</guid><link>https://weworkremotely.com/x</link></item></channel></rss>"""
    (j,) = weworkremotely.parse(xml)
    assert j["company"] == "Acme" and j["title"] == "Senior DevOps Engineer" and "Kubernetes" in j["description"]


def test_workingnomads():
    data = [{"url": "https://wn/1", "title": "SRE", "company_name": "F", "category_name": "Sysadmin",
             "tags": "aws,linux", "location": "Europe", "pub_date": "2026-11-24T00:00:00Z", "description": "x"},
            {"url": "https://wn/2", "title": "SRE", "company_name": "F", "category_name": "Marketing"}]
    (j,) = workingnomads.parse(data)
    assert j["tags"] == ["aws", "linux"]


def test_hn():
    assert hn.latest_thread_id({"hits": [{"title": "Who wants to be hired?", "objectID": "1"},
                                         {"title": "Ask HN: Who is hiring? (November 2026)", "objectID": "2"}]}) == "2"
    data = {"id": 2, "children": [
        {"id": 10, "created_at_i": 1764000000, "text": "Acme | Senior SRE | REMOTE (EU) | Full-time<p>We run Kubernetes.</p>"},
        {"id": 11, "created_at_i": 1764000000, "text": "Beta | Frontend | REMOTE<p>React.</p>"},
        {"id": 12, "created_at_i": 1764000000, "text": "Gamma | DevOps | NYC onsite<p>No remote.</p>"},
        {"id": 13, "created_at_i": 1764000000, "text": "Rootly | https://rootly.com | SF Bay, Toronto, APAC, Remote | engineering, product<p>We build incident infrastructure.</p>"},
    ]}
    j, j2 = hn.parse_thread(data)
    assert j2["title"] == "Infrastructure role (see post)" and "http" not in j2["location"]
    assert j["company"] == "Acme" and j["title"] == "Senior SRE" and "EU" in j["location"]
