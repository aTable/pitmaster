function getData() {
  return fetch("https://192.168.1.96:30002").then((res) => res.json());
}

function initializeChart(res) {
  const labels = res.map((x) => dayjs(x.recorded_at_utc).format("MMM DD hh:mm:ss A"));
  const values = res.map((x) => x.celsius);
  const data = {
    labels: labels,
    datasets: [
      {
        label: "The Pit",
        backgroundColor: "rgb(33, 37, 41)",
        borderColor: "rgb(33, 37, 41)",
        data: values,
      },
    ],
  };

  const config = {
    type: "line",
    data: data,
    options: {},
  };
  const allReadings = new Chart(document.getElementById("all-readings"), config);
}

getData()
  .then((res) => initializeChart(res))
  .catch((err) => {
    const p = document.createElement("p");
    p.textContent = err.toString();
    document.body.appendChild(p);
  });
