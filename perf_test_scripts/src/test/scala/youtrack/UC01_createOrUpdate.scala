package youtrack

import io.gatling.core.Predef._
import io.gatling.http.Predef._
import scala.concurrent.duration._
import scala.util.Random

/**
 * Scenario:
 * 1) List issues
 * 2) Either open + update random field OR create a new issue
 *
 * All flows are wrapped in a script-level transaction and each user action
 * has its own transaction group.
 */
class UC01_createOrUpdate extends Simulation {

  private val random = new Random()

  private def randomText(minLen: Int, maxLen: Int): String = {
    val words = Array(
      "issue", "workflow", "dashboard", "backlog", "priority", "validation",
      "integration", "latency", "search", "notification", "comment", "project",
      "owner", "reporter", "activity", "update", "release", "iteration",
      "filter", "sprint", "board", "state", "analysis", "tracking"
    )
    val targetLen = minLen + random.nextInt((maxLen - minLen + 1).max(1))
    val builder = new StringBuilder()

    while (builder.length < targetLen) {
      if (builder.nonEmpty) builder.append(' ')
      builder.append(words(random.nextInt(words.length)))
    }

    builder.toString().take(targetLen)
  }

  // Config
  val baseUrl        = sys.env.getOrElse("YOUTRACK_URL", "http://youtrack:8080")
  val token          = sys.env.getOrElse("YOUTRACK_TOKEN", "")
  val project        = sys.env.getOrElse("YOUTRACK_PROJECT", "DEMO")
  val users          = sys.env.getOrElse("PERF_USERS", "10").toInt
  val durationSec    = sys.env.getOrElse("PERF_DURATION", "120").toInt
  val createRatioPct = sys.env.getOrElse("PERF_CREATE_RATIO", "30").toDouble

  val httpProtocol = http
    .baseUrl(baseUrl)
    .header("Authorization", s"Bearer $token")
    .header("Accept", "application/json")
    .contentTypeHeader("application/json")
    .shareConnections

  // Feeders
  val userFeeder           = csv("users.csv").random
  val updateFieldFeeder    = csv("update_fields.csv").random
  val createTemplateFeeder = csv("issue_create_templates.csv").random

  val pageFeeder = Iterator.continually(Map(
    "skip" -> (random.nextInt(250) * 20).toString
  ))

  // Actions
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

  val updateIssueAction = group("Action: Update Random Field") {
    feed(updateFieldFeeder)
      .exec { session =>
        val minLen = session("minLen").as[String].toInt
        val maxLen = session("maxLen").as[String].toInt
        session.set("updateValue", randomText(minLen, maxLen))
      }
      .doSwitch("${fieldName}")(
        "summary" -> exec(
          http("POST update summary")
            .post("/api/issues/${randomIssueId}")
            .queryParam("fields", "id,idReadable,summary")
            .body(StringBody("""{"summary":"${updateValue}"}"""))
            .check(status.is(200))
        ),
        "description" -> exec(
          http("POST update description")
            .post("/api/issues/${randomIssueId}")
            .queryParam("fields", "id,idReadable,description")
            .body(StringBody("""{"description":"${updateValue}"}"""))
            .check(status.is(200))
        ),
        "comment" -> exec(
          http("POST add comment")
            .post("/api/issues/${randomIssueId}/comments")
            .queryParam("fields", "id,text")
            .body(StringBody("""{"text":"${updateValue}"}"""))
            .check(status.is(200))
        )
      )
  }

  val createIssueAction = group("Action: Create New Issue") {
    feed(createTemplateFeeder)
      .exec { session =>
        val actor = session("login").as[String]
        val summaryBase = session("summaryTemplate").as[String]
        val descriptionBase = session("descriptionTemplate").as[String]

        val summary = s"$summaryBase ${randomText(20, 60)}"
        val description = s"$descriptionBase ${randomText(180, 420)} actor:$actor"

        session
          .set("newSummary", summary)
          .set("newDescription", description)
      }
      .exec(
        http("POST create issue")
          .post("/api/issues")
          .queryParam("fields", "id,idReadable,summary")
          .body(StringBody(session =>
            s"""{"project":{"shortName":"$project"},"summary":"${session("newSummary").as[String]}","description":"${session("newDescription").as[String]}"}"""
          ))
          .check(status.is(200))
            .check(jsonPath("$.idReadable").saveAs("createdIssueId"))
      )
  }

  val scriptFlow = group("Script: BrowseAndWrite") {
    feed(userFeeder)
      .exec(listIssuesAction)
      .randomSwitch(
        createRatioPct -> exec(createIssueAction),
        (100.0 - createRatioPct) -> doIf(session => session.contains("randomIssueId")) {
          exec(openIssueAction).exec(updateIssueAction)
        }
      )
      .pace(8000.millis, 9000.millis)
  }

  val scn = scenario("Browse And Write")
    .forever {
      exec(scriptFlow)
    }

  setUp(
    scn.inject(rampUsers(users).during(20.seconds))
  )
    .protocols(httpProtocol)
    .maxDuration(durationSec.seconds)
}
