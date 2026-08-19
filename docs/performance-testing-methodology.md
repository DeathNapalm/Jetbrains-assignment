# Performance Testing Methodology (Draft)

## 1. Purpose and scope

This document defines the first-pass methodology for evaluating the performance and scalability of the YouTrack Server instance under realistic user behavior. The objective is to determine whether the target system can support the expected production-like workload, identify performance headroom before degradation begins, and estimate the practical breaking point under the constrained environment described in the assignment.

This methodology follows standard performance-testing practices:

- establish the target system and workload model,
- validate a stable baseline,
- run controlled load and stress scenarios,
- measure the relevant system and API-level metrics,
- compare results against objective SLOs,
- document conclusions and evidence.

## 2. Target system description

### 2.1 Application under test

- Product: JetBrains YouTrack Server
- Version: 2026.1.13456
- Deployment: server installation, default configuration, with a 60-day trial license for 100 users
- Core workload: issue management operations in a large tracker instance with frequent issue reads, writes, searches, and updates

### 2.2 Environment assumptions

The target environment is the stated reference setup for the assignment:

- CPU: at least 2 vCPU cores
- Memory: at least 3 GB RAM
- Storage and database: default application settings unless otherwise required by the test plan
- Load generator: can run on the same machine or a separate machine; the test plan should prefer a separate machine when available to avoid generator-side contention

### 2.3 Test data set

The system is populated with a realistic data volume intended to stress search, listing, issue retrieval, and write paths:

- 1 project: Demo
- 100 users
- 100,000 issues
- Users are added to the project team and the Registered Users group as required by the assignment
- Each issue includes a summary and description; issue creation is distributed across different users

### 2.4 Workload model

The performance scenario is modeled from the assignment and represents average end-user behavior over one hour. A representative user is assumed to perform the following actions:

- Create or update 10 issues per hour
- Open approximately 30 issues for reading per hour
- Execute about 10 searches per hour
- Mix read and write operations across the same issue set in a realistic way

This workload should be applied across a concurrency model that targets the required active-user load, with the primary scenario centered on 100 concurrent active users. The workload should not be limited to a single API call pattern; it must reflect realistic user flows, including issue list loading, issue detail retrieval, and issue modification flows.

## 3. Performance objectives

The test program is designed to answer the following questions:

1. Can the tracker withstand 100 concurrent active users under the specified resource constraints?
2. How much headroom exists before the system shows performance degradation?
3. Is there a clear breaking point under the selected resource profile, or do external factors prevent the system from reaching it?

The assignment also defines the degradation signal: at least one SLO violation indicates the onset of performance degradation.

## 4. Test types to execute

### 4.1 Baseline validation

Purpose: confirm the system is healthy and stable before applying load.

- Run with a small number of virtual users (for example 1–10), or no production-like concurrency
- Observe API responsiveness and confirm no obvious errors or configuration problems
- Verify that the target endpoints and authorization flow are functional
- Capture initial CPU, memory, and request latency baselines

### 4.2 Load test at target concurrency

Purpose: evaluate the system at the assignment target of 100 concurrent active users.

- Use a realistic end-user mix of reads, writes, and searches
- Maintain a fixed workload over a controlled steady-state window
- Monitor whether the system remains within SLO thresholds for the full run

### 4.3 Headroom / saturation test

Purpose: identify the point at which the system begins to degrade.

- Increment user concurrency gradually above the target load
- Track p90 latency, throughput, error rate, and resource saturation
- Define the headroom as the highest load level before the first sustained SLO breach

### 4.4 Stress test

Purpose: push the system beyond the stable operating zone to measure breaking behavior.

- Increase concurrency to a level above the expected headroom limit
- Evaluate whether the system fails gracefully or exhibits runaway latency, elevated error rate, or resource exhaustion
- Record whether the platform reaches a plateau, degrades, or becomes unavailable

### 4.5 Soak / endurance test (recommended)

Purpose: surface slow leaks, memory accumulation, thread exhaustion, or background processing issues.

- Run a moderate sustained load for a longer duration, such as 30–60 minutes
- Watch for gradual degradation in latency or throughput over time
- Confirm that the system remains stable beyond short bursts

## 5. Test scenario and execution flow

### 5.1 Test flow structure

Each performance run should include the following phases:

1. Warm-up period
   - Start with a short low-load phase to avoid measuring cold-start effects
   - Allow caches, connection pools, and background initialization to reach steady behavior

2. Ramp-up
   - Increase active users gradually to the target load or next step in the load matrix
   - Keep the ramp deterministic and repeatable between runs

3. Steady-state observation
   - Hold the desired concurrency for a fixed window to collect statistically meaningful metrics
   - Usually 10–20 minutes for a representative test, extendable for soak tests

4. Ramp-down / cool-down
   - Reduce load gradually to prevent abrupt server teardown effects from contaminating the results

### 5.2 Recommended load profile

| Scenario | Concurrent users | Duration | Purpose |
| --- | ---: | ---: | --- |
| Baseline | 1-10 | 5-10 min | Functional validation and calibration |
| Target load | 100 | 15-60 min | Check compliance with assignment SLOs |
| Headroom | 120, 150, 200, ... | 10-15 min per step | Find degradation onset |
| Stress | above headroom | 10-30 min | Estimate breaking point |
| Soak | moderate sustained load | 30-60 min | Detect degradation over time |

The load schedule should be documented in a way that allows repeatability. The same mix of issue reading, issue creation/update, and searching should be used for each scenario.

## 6. Metrics to be measured

The framework should collect both application-layer and infrastructure-layer metrics, because end-user response time alone is not sufficient to explain poor behavior.

### 6.1 API and user-facing metrics

- Response time per endpoint
- p50, p90, p95 response time
- Request throughput (requests per second)
- Success/error rate by endpoint and overall
- Concurrent virtual users and active requests
- HTTP status distribution

### 6.2 Business-operation metrics

- Number of issue read events
- Number of issue updates/comments/commands applied
- Number of search requests
- Number of issue-create operations
- Mean and peak action latency

### 6.3 System resource metrics

- CPU utilization
- Memory utilization
- Heap and GC activity
- Database CPU and I/O
- Network throughput and latency
- Thread pool / connection pool saturation

### 6.4 Recommended metrics by endpoint

The assignment specifically requires the following endpoint-level monitoring:

- GET /api/sortedIssues
- GET /api/issue/{id}?fields=...
- POST /api/issuesGetter?fields=...

For these endpoints, measure:

- p90 latency
- p95 latency (recommended for deeper diagnosis)
- absolute minimum and maximum latency
- request count
- HTTP 500 rate

## 7. SLOs and acceptance criteria

The assignment defines the degradation criteria. A violation of at least one of the following values indicates performance degradation:

- 90th percentile response time for GET /api/sortedIssues <= 500 ms
- 90th percentile response time for GET /api/issue/{id}?fields=... <= 500 ms
- 90th percentile response time for POST /api/issuesGetter?fields=... <= 1000 ms
- HTTP 500 error rate <= 1%

These SLOs should be treated as the primary pass/fail threshold for the target workload. For the final report, performance degradation should be reported as the first sustained load level where one or more SLO conditions are breached, not only the peak concurrency level that triggers a single spike.

## 8. Test execution procedure

1. Prepare the target environment with the YouTrack Server configuration required by the assignment.
2. Inject the required data set: 1 project, 100 users, and 100,000 issues.
3. Verify default access and permissions for all users.
4. Configure the load generator with the intended user model and concurrency profile.
5. Run a baseline test to validate instrumented endpoints and authentication.
6. Execute the target-load scenario at 100 concurrent active users.
7. Run headroom tests at increasing concurrency levels until the system approaches or exceeds the performance limits.
8. If needed, run a stress or soak test to confirm the breaking point or the absence of a clear break condition.
9. Capture all metrics in a structured format for later reporting.
10. Repeat any run only when the initial results are inconclusive or the environment is clearly unstable.

## 9. Data collection and analysis method

### 9.1 Data sampling

- Collect metrics for the full run, including ramp-up and steady-state periods
- Exclude warm-up from comparative SLO analysis unless the warm-up is part of the controlled test plan
- Keep runtime and load configuration consistent across repeated tests

### 9.2 Analysis approach

- Compare request latency percentiles against the SLO thresholds
- Check the distribution of errors by endpoint, not only total error count
- Correlate rising latency with CPU, memory, and DB pressure
- Identify whether the system saturates due to application logic, database contention, or infrastructure limits
- Distinguish between a true breaking point and an artificial bottleneck caused by the test harness or environment design

### 9.3 Result interpretation

- If latency remains within the SLO envelope at 100 concurrent users, the system passes the target load scenario
- If latency begins to exceed the SLO at a higher concurrency level, that concurrency indicates the operating headroom
- If the platform cannot be pushed past a certain level because of a system-internal or infrastructure limit, the report should explain the limiting factor and whether it prevented the true breaking point from being reached

## 10. Reporting structure

The final report should include:

- description of the system under test,
- environment details and data set,
- workload model and user behavior simulation,
- test matrix and scenario schedule,
- list of executed tests,
- metrics and graphs,
- SLO comparison,
- conclusions about target capacity, headroom, and breaking point,
- any caveats or external constraints affecting the result.

## 11. Recommended first-draft test matrix

The first pass should prioritize clarity over breadth. A practical initial matrix is:

| Test | Users | Duration | Expected purpose |
| --- | ---: | ---: | --- |
| Baseline | 10 | 10 min | Confirm readiness |
| Target load | 100 | 20-30 min | Validate assignment SLOs |
| Headroom 1 | 150 | 15 min | Look for early degradation |
| Headroom 2 | 200 | 15 min | Quantify saturation region |
| Stress | 250+ | 10-20 min | Estimate breaking point |
| Soak | 75-100 | 30-60 min | Check stability over time |

This provides a strong first iteration while keeping the total execution time manageable and avoiding excessive reruns.

## 12. Risks and caveats

- A performance test is only as valid as the environment fidelity; differences between the test and production environment can distort the outcome.
- Real user behavior is rarely uniform; bursts of search activity, issue updates, and mass reads can create transient conditions not seen in a flat steady-state run.
- Exceeding some concurrency levels may trigger platform bottlenecks such as database locks, request queuing, or connection limits rather than purely application defects.
- A single outlier should not be interpreted as a breaking point unless it is sustained and repeated under the same test conditions.

## 13. Summary

This draft methodology creates a repeatable, evidence-driven way to evaluate the performance of the YouTrack Server under realistic load. It combines a target-user workload model, endpoint-level SLO checks, resource instrumentation, and a staged execution plan that moves from baseline validation to load, headroom, and stress testing. The result is a methodology suitable for a first performance-testing report and a good foundation for deeper tuning or follow-up benchmarking.

## 14. Reference patterns used in this draft

The structure above follows common industry patterns for performance testing documentation and is aligned with the assignment requirements, including:

- target system definition,
- data and workload characterization,
- scenario-based test execution,
- latency/error/SLO thresholds,
- resource metrics and interpretation,
- headroom and breaking-point analysis.

The methodology is intentionally written as a practical first draft that can be expanded with real run data, graphs, and final conclusions once the test execution phase is complete.
