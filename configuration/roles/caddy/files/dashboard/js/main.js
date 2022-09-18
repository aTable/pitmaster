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
    options: {
      plugins: {
        autocolors: false,
        annotation: {
          annotations: {
            box1: {
              type: "box",
              xMin: 0,
              xMax: 100000000000000,
              yMin: 107.1,
              yMax: 121.2,
              backgroundColor: "rgba(0, 151, 52, 0.2)",
            },
          },
        },
      },
      scales: {
        x: {
          title: {
            display: true,
            text: "Time",
          },
        },
        y: {
          beginAtZero: true,
          min: 0,
          max: 200,
          title: {
            display: true,
            text: "Celsius",
          },
        },
      },
    },
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
