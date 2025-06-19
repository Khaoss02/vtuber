<template>
  <div class="mode-selector">
    <button @click="$emit('change','2d')">Modo 2D</button>
    <button @click="$emit('change','3d')">Modo 3D</button>
  </div>
</template>
