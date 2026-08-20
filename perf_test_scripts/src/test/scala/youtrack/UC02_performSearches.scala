package youtrack

import io.gatling.core.Predef._
import io.gatling.http.Predef._
import scala.concurrent.duration._

/**
 * Scenario:
 * Random users execute random search queries from CSV.
 * Includes script-level and action-level transaction groups.
 */
class UC02_performSearches extends Simulation {

  val baseUrl     = sys.env.getOrElse("YOUTRACK_URL", "http://youtrack:8080")
  val token       = sys.env.getOrElse("YOUTRACK_TOKEN", "")
  val users       = sys.env.getOrElse("PERF_USERS", "10").toInt
  val durationSec = sys.env.getOrElse("PERF_DURATION", "120").toInt

  val httpProtocol = http
    .baseUrl(baseUrl)
    .header("Authorization", s"Bearer $token")
    .header("Accept", "application/json")
    .contentTypeHeader("application/json")
    .shareConnections

  val userFeeder = csv("users.csv").random
  val searchFeeder = csv("search_queries.csv").random

  val searchAction = group("Action: Perform Search") {
    feed(searchFeeder)
      .exec(
        http("POST issuesGetter search")
          .post("/api/issuesGetter")
          .queryParam("fields", "id,idReadable,summary,updated")
          .body(
            StringBody(
              """{"query":"${query}","$top":20,"$skip":0}"""
            )
          )
          .check(status.is(200))
      )
  }

  val scriptFlow = group("Script: Search") {
    feed(userFeeder)
      .exec(searchAction)
      .pace(1750.millis, 2250.millis)
  }

  val scn = scenario("Search Issues")
    .forever {
      exec(scriptFlow)
    }

  setUp(
    scn.inject(rampUsers(users).during(20.seconds))
  )
    .protocols(httpProtocol)
    .maxDuration(durationSec.seconds)
}
