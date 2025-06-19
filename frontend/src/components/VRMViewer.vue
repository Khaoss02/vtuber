<template>
  <canvas ref="canvas"></canvas>
</template>
<script>
import { defineComponent, onMounted, ref } from 'vue';
import { Scene, PerspectiveCamera, WebGLRenderer } from 'three';
import { VRM, VRMUtils } from '@pixiv/three-vrm';

export default defineComponent({
  methods: {
    setViseme(viseme, emotion) {
      // Mapear visema/emoción a blendShapes
      if (!this.vrm) return;
      const bs = this.vrm.blendShapeProxy;
      bs.setValue(viseme, 1.0);
      // Mapea emociones a blendShapes adicionales si quieres
      bs.update();
    }
  },
  setup() {
    const canvas = ref();
    let vrm;
    onMounted(async () => {
      const renderer = new WebGLRenderer({ canvas: canvas.value, alpha: true });
      const scene = new Scene();
      const camera = new PerspectiveCamera(35, window.innerWidth/window.innerHeight, 0.1, 20);
      camera.position.set(0,1.4,1.8);

      const array = await fetch('/models/avatar.vrm').then(r=>r.arrayBuffer());
      vrm = await VRM.from(array);
      VRMUtils.rotateY(vrm.scene, Math.PI);
      scene.add(vrm.scene);

      const animate = () => {
        requestAnimationFrame(animate);
        vrm.update(0);
        renderer.render(scene, camera);
      };
      animate();
    });
    return { canvas };
  }
});
</script>
