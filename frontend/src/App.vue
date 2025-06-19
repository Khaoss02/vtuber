<template>
  <ModeSelector @change="mode = $event" />
  <div v-if="mode==='2d'">
    <Live2DWidget ref="avatar2d" />
  </div>
  <div v-else-if="hasVrm">
    <VRMViewer ref="avatar3d" />
  </div>
  <div v-else class="no-vrm">
    🤖 No se encontró modelo 3D. Usando modo 2D.
  </div>
</template>

<script>
import { ref, onMounted } from 'vue';
import ModeSelector from './components/ModeSelector.vue';
import Live2DWidget from './components/Live2DWidget.vue';
import VRMViewer from './components/VRMViewer.vue';

export default {
  components: { ModeSelector, Live2DWidget, VRMViewer },
  setup() {
    const mode = ref('2d');
    const hasVrm = ref(false);
    onMounted(async () => {
      hasVrm.value = await fetch('/models/avatar.vrm', { method: 'HEAD' })
                        .then(r=>r.ok).catch(()=>false);
    });
    // WebSocket cliente
    const ws = new WebSocket("ws://localhost:8000/ws");
    ws.binaryType = 'arraybuffer';
    ws.onmessage = ({ data }) => {
      const msg = JSON.parse(data);
      const { viseme, emotion, text, mode: m } = msg;
      mode.value = m;
      if (m==='2d') this.$refs.avatar2d.setViseme(viseme, emotion);
      else           this.$refs.avatar3d.setViseme(viseme, emotion);
      // Mostrar text en UI...
    };

    return { mode, hasVrm };
  }
}
</script>
