# Team Charter

## 1. Goals

**What does a good result look like for our team?**

Effectively applying the ETL pipeline and getting an actionable, informative conclusion from our data analysis.

**What does each person want to get out of this?**

A better understanding of Python ETL, working with APIs, and stronger team collaboration skills.

**What limits our time?**

Projects to complete in other classes.

**What would make this a bad experience, and what will we do to avoid it?**

All of the work falling on one or two people. We will avoid this by clearly splitting up responsibilities and maintaining clear communication.

## 2. Who does what

There are four jobs, matched to where the points are. Each job has an owner, who makes sure it gets done, and a backup, who can step in if the owner is sick or swamped. The owner does not have to do all of it alone, but the owner is the person we ask.

| Role | Owner | Responsible for | Done when | Grade area |
| --- | --- | --- | --- | --- |
| Cleaning + decision log | Shaddai | The cleaning functions, the SKU mapping table, and the decision log | One function takes the raw files and returns clean tables. The log lists every decision and how many rows it touched | Data cleaning, 25% |
| Weather API + join | Amudhan | The API call with retries, parsing it into a DataFrame, timezone alignment, and the checked join to sales | One function returns daily weather. The join passes a row-count check. The API base URL is cited | Weather API, 15% |
| Analysis Q1–Q5 | Dylan | The five answers: code, a number, and a written finding for each. Question 5 uses the SQLite database | Every question has code, a number, and a paragraph | Questions, 30% |
| Charts + presentation | Shared | At least six plots with message titles, the six-minute talk, and the README | Six labeled plots, and the talk has been rehearsed once | Visualizations, 15% |

## 3. Who owns each question

Every question gets an owner, who writes it, and a reviewer, who is someone else and tries to break it.

- Is the baseline stated?
- Does the row count check out?
- Does the chart say what its title says?

Q1 and Q3 are the critical path. Q1 needs clean dates and Q3 needs the weather API. Everything else can run in parallel, so get those two moving first.

## 4. How we work together

**Where do we talk, and how fast do we answer?**

We have our group chat and we can easily communicate there.

**When do we meet outside class?**

Sundays after 5pm on Zoom.

**How do we decide when we disagree?**

We talk about disagreements in the Sunday meetings and in the group chat.

**What do we do if someone goes quiet?**

We check in on them to see if everything is going alright.
