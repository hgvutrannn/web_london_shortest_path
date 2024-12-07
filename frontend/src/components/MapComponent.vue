<template>
  <div style="display: flex;">
    <!-- Form Section -->
    <div style="width: 30%; padding: 20px;">
      <h2>Travel Planner</h2>
      <form @submit.prevent="fetchRoute">
        <div>
          <label for="startStation">Start Station:</label>
          <select v-model="startStation" id="startStation" required>
            <option disabled value="">Select a station</option>
            <option v-for="station in stations" :key="station" :value="station">
              {{ station }}
            </option>
          </select>
        </div>
        <div>
          <label for="endStation">End Station:</label>
          <select v-model="endStation" id="endStation" required>
            <option disabled value="">Select a station</option>
            <option v-for="station in stations" :key="station" :value="station">
              {{ station }}
            </option>
          </select>
        </div>
        <button type="submit">Get Route</button>
      </form>
      <div v-if="route">
        <h3>Travel Guide</h3>
        <p><strong>Path:</strong> {{ route.path.join(" → ") }}</p>
        <p><strong>Distance:</strong> {{ route.distance }}</p>
        <p><strong>Line Change Information:</strong></p>
        <p v-for="(instruction, index) in route.guide" :key="index">
          {{ instruction }}
        </p>
      </div>
      <div v-if="error" style="color: red;">{{ error }}</div>
    </div>

    <!-- Map Section -->
    <div style="width: 65%; padding: 20px;">
      <section><h1>London Tube Lines with Distances (in km)</h1></section>
      <section>
        <div ref="mapContainer">
          <img
            :src="'data:image/png;base64,' + figure"
            alt="Tube Map"
            style="width: 100%;"
          />
        </div>
      </section>
      <section>
        <!-- Reset Button -->
        <button @click="resetMap" style="margin-top: 10px;">Reset Map</button>
      </section>
    </div>
  </div>
</template>

<script>
import axios from "axios";
import Panzoom from "@panzoom/panzoom";

export default {
  data() {
    return {
      figure: null, // Base64 map image
      startStation: "",
      endStation: "",
      stations: [], // List of all stations
      route: null, // Stores the travel guideline
      error: null,
      panzoomInstance: null,
    };
  },
  methods: {
    async fetchStations() {
      try {
        const response = await axios.get("http://127.0.0.1:8000/stations");
        this.stations = response.data.stations;
      } catch (err) {
        console.error("Error fetching stations:", err);
      }
    },
    async fetchMap() {
      try {
        const response = await axios.get("http://127.0.0.1:8000/");
        this.figure = response.data.figure;
        this.$nextTick(() => {
          this.initPanzoom(); // Initialize Panzoom after the image is loaded
        });
      } catch (err) {
        console.error("Error fetching map:", err);
      }
    },
    async fetchRoute() {
      try {
        const response = await axios.post(
          "http://127.0.0.1:8000/route",
          new URLSearchParams({
            start_station: this.startStation,
            end_station: this.endStation,
          })
        );
        if (response.data.error) {
          this.error = response.data.error;
          this.route = null;
        } else {
          this.route = {
            path: response.data.path,
            distance: response.data.distance,
            guide: response.data.guide,
          };

          // Update the figure with the new Base64 image from the response
          console.log(response.data.figure)
          if(response.data.figure)
            this.figure = response.data.figure;
          this.error = null;
        }
      } catch (err) {
        console.error("Error fetching route:", err);
        this.error = "Unable to fetch route.";
      }
    },
    initPanzoom() {
      const mapContainer = this.$refs.mapContainer;
      this.panzoomInstance = Panzoom(mapContainer, {
        maxScale: 15, // Maximum zoom level
        minScale: 1, // Minimum zoom level
      });
      mapContainer.addEventListener("wheel", this.panzoomInstance.zoomWithWheel);
    },
    resetMap() {
      // Use the Panzoom reset method
      if (this.panzoomInstance) {
        this.panzoomInstance.reset(); // Reset the map to its initial position and zoom level
      }
    },
  },
  mounted() {
    this.fetchMap();
    this.fetchStations(); // Fetch the station list when the component mounts
  },
  beforeUnmount() {
    if (this.panzoomInstance) {
      this.panzoomInstance.destroy();
    }
  },
};
</script>

<style>
body {
  font-family: Arial, sans-serif;
  margin: 0;
}
form {
  margin-bottom: 20px;
}
form div {
  margin-bottom: 10px;
}
form label {
  display: block;
  font-weight: bold;
}
form select {
  width: 100%;
  padding: 5px;
  margin-top: 5px;
}
button {
  padding: 10px 20px;
  background-color: #007bff;
  color: white;
  border: none;
  cursor: pointer;
}
button:hover {
  background-color: #0056b3;
}
h3, p, ul {
  text-align: left;
  margin: 10px 0;
}
</style>