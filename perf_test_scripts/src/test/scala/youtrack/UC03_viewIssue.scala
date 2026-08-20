package youtrack

import io.gatling.core.Predef._
import io.gatling.http.Predef._
import scala.concurrent.duration._
import scala.util.Random

/**
 * Scenario:
 * 1) List issues
 * 2) Open one random issue from the returned list
 */
class UC03_viewIssue extends Simulation {

  private val random = new Random()

  val baseUrl     = sys.env.getOrElse("YOUTRACK_URL", "http://youtrack:8080")
  val token       = sys.env.getOrElse("YOUTRACK_TOKEN", "")
  val project     = sys.env.getOrElse("YOUTRACK_PROJECT", "DEMO")
  val users       = sys.env.getOrElse("PERF_USERS", "10").toInt
  val durationSec = sys.env.getOrElse("PERF_DURATION", "120").toInt

  val httpProtocol = http
    .baseUrl(baseUrl)
    .header("Authorization", s"Bearer $token")
    .header("Accept", "application/json")
    .contentTypeHeader("application/json")
    .shareConnections

  val userFeeder = csv("users.csv").random

  val pageFeeder = Iterator.continually(Map(
    "skip" -> (random.nextInt(250) * 20).toString
  ))

  val listIssuesAction = group("Action: List Issues") {
    feed(pageFeeder)
      .exec(
        http("GET issue list")
          .get("/api/issues")
          .queryParam("query", s"project: $project")
          .queryParam("fields", "id,idReadable,summary,updated")
          .queryParam("$top", "20")
          .queryParam("$skip", "${skip}")
          .check(status.is(200))
          .check(jsonPath("$[*].idReadable").findRandom.optional.saveAs("randomIssueId"))
      )
  }

  val openIssueAction = group("Action: Open Random Issue") {
    exec(
      http("GET issue - ${randomIssueId}")
        .get("/api/issues/${randomIssueId}")
        .queryParam("fields", "id,idReadable,summary,description,updated")
        .check(status.is(200))
        .check(jsonPath("$.idReadable").exists)
    )
  }

  val scriptFlow = group("Script: ViewIssue") {
    feed(userFeeder)
      .exec(listIssuesAction)
      .doIf(session => session.contains("randomIssueId")) {
        exec(openIssueAction)
      }
      .pace(2100.millis, 2700.millis)
  }

  val scn = scenario("View Issue")
    .forever {
      exec(scriptFlow)
    }

  setUp(
    scn.inject(rampUsers(users).during(20.seconds))
  )
    .protocols(httpProtocol)
    .maxDuration(durationSec.seconds)
}