<template>
  <canvas ref="live2dcanvas"></canvas>
</template>
<script>
import { loadLive2DModel, setExpression, setViseme } from 'z-waif-sdk'; // ajusta import
export default {
  methods: {
    setViseme(viseme, emotion) {
      setViseme(this.$refs.live2dcanvas, viseme);
      setExpression(this.$refs.live2dcanvas, emotion);
    }
  },
  mounted() {
    loadLive2DModel(this.$refs.live2dcanvas, {
      model: '/live2d-models/mao_pro/mao_pro.model3.json',
      moc:   '/live2d-models/mao_pro/mao_pro.moc3',
      physics:'/live2d-models/mao_pro/mao_pro.physics3.json',
      pose:   '/live2d-models/mao_pro/mao_pro.pose3.json',
      textures: ['/live2d-models/mao_pro.4096/texture_00.png']
    });
  }
}
</script>
