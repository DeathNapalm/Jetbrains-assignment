package youtrack

import io.gatling.core.Predef._
import io.gatling.http.Predef._
import scala.concurrent.duration._

/**
 * Simulates users periodically browsing YouTrack issues:
 *   Transaction 1 – open the issue list (paginated, random offset)
 *   Transaction 2 – open a single issue from that list
 */
class BrowseIssuesSimulation extends Simulation {

  // ── Config ────────────────────────────────────────────────────────────────
  val baseUrl     = sys.env.getOrElse("YOUTRACK_URL",   "http://youtrack:8080")
  val token       = sys.env.getOrElse("YOUTRACK_TOKEN", "")
  val project     = sys.env.getOrElse("YOUTRACK_PROJECT", "DEMO")
  val users       = sys.env.getOrElse("PERF_USERS",    "10").toInt
  val durationSec = sys.env.getOrElse("PERF_DURATION", "120").toInt

  // ── HTTP protocol ─────────────────────────────────────────────────────────
  val httpProtocol = http
    .baseUrl(baseUrl)
    .header("Authorization", s"Bearer $token")
    .header("Accept", "application/json")
    .contentTypeHeader("application/json")
    .shareConnections

  // ── Feeders ───────────────────────────────────────────────────────────────
  // Random user from users.csv  (login column → used only for labelling/logging)
  val userFeeder = csv("users.csv").random

  // Random page offset so different users hit different pages
  val pageFeeder = Iterator.continually(Map(
    "skip" -> (scala.util.Random.nextInt(1000) * 20).toString
  ))

  // ── Transactions ──────────────────────────────────────────────────────────

  /** Transaction 1: fetch a page of issues */
  val listIssues = group("List Issues") {
    feed(pageFeeder)
    .exec(
      http("GET issue list")
        .get("/api/issues")
        .queryParam("query",  s"project: $project")
        .queryParam("fields", "id,idReadable,summary,reporter(login),created,updated")
        .queryParam("$top",   "20")
        .queryParam("$skip",  "#{skip}")
        .check(status.is(200))
        .check(jsonPath("$[0].idReadable").saveAs("firstIssueId"))
        .check(jsonPath("$[*].idReadable").findRandom.saveAs("randomIssueId"))
    )
  }

  /** Transaction 2: open one issue from the list */
  val openIssue = group("Open Issue") {
    exec(
      http("GET single issue - #{randomIssueId}")
        .get("/api/issues/#{randomIssueId}")
        .queryParam("fields", "id,idReadable,summary,description,reporter(login),assignee(login),created,updated,comments(id,text)")
        .check(status.is(200))
        .check(jsonPath("$.idReadable").exists)
    )
  }

  // ── Scenario ──────────────────────────────────────────────────────────────
  val browseScenario = scenario("Browse Issues")
    .feed(userFeeder)
    .forever {
      exec(listIssues)
        .pause(1.second, 3.seconds)   // think time between transactions
        .exec(openIssue)
        .pause(3.seconds, 8.seconds)  // think time before next browse cycle
    }

  // ── Injection ─────────────────────────────────────────────────────────────
  setUp(
    browseScenario.inject(
      rampUsers(users).during(20.seconds)   // ramp up over 20 s
    )
  )
    .protocols(httpProtocol)
    .maxDuration(durationSec.seconds)
    .assertions(
      global.responseTime.percentile(95).lt(2000),  // 95th pct < 2 s
      global.successfulRequests.percent.gt(95)       // >95% success
    )
}
