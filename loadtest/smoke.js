import http from "k6/http";
import { check, sleep } from "k6";

const baseUrl = __ENV.BASE_URL || "http://localhost:5000";

export const options = {
  vus: 5,
  duration: "20s",
  thresholds: {
    http_req_failed: ["rate<0.01"],
    http_req_duration: ["p(95)<500"],
  },
};

export default function () {
  const response = http.get(`${baseUrl}/api/greeting`);
  check(response, {
    "greeting returns 200": (res) => res.status === 200,
    "response contains a greeting": (res) => res.body.includes("Hello from Lab 3"),
  });
  sleep(0.2);
}
