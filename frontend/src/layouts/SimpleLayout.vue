<template>
  <div class="simple-layout">
    <router-view />
  </div>
</template>

<script setup>
</script>

<style scoped>
.simple-layout {
  min-height: 100vh;
  background: var(--bg-page, #f0f2f5);
}
</style>