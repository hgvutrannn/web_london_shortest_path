<template>
  <div id="app">
    <MapComponent />
  </div>
</template>

<script>
import MapComponent from "./components/MapComponent.vue";

export default {
  name: "App",
  components: {
    MapComponent,
  },
};
</script>

<style>
#app {
  text-align: center;
}
</style>