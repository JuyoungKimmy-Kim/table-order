<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'

// 방명록 그림판 모달. Pointer Events 로 마우스·터치·펜을 통합 처리한다.
// 저장 시 canvas 를 PNG DataURL 로 인코딩해 부모에 전달한다.
const emit = defineEmits(['save', 'close'])
const props = defineProps({
  saving: { type: Boolean, default: false },
})

const PALETTE = ['#1f2937', '#dc2626', '#2563eb', '#059669', '#f59e0b', '#db2777']
const CANVAS_W = 320
const CANVAS_H = 240

const canvasRef = ref(null)
const color = ref(PALETTE[0])
const lineWidth = ref(4)
const isEraser = ref(false)
const authorName = ref('')
const hasDrawn = ref(false)

let ctx = null
let drawing = false

function initCanvas() {
  const canvas = canvasRef.value
  // 디바이스 픽셀 비율만큼 실제 해상도를 키워 선명하게 그린다.
  const dpr = window.devicePixelRatio || 1
  canvas.width = CANVAS_W * dpr
  canvas.height = CANVAS_H * dpr
  canvas.style.width = CANVAS_W + 'px'
  canvas.style.height = CANVAS_H + 'px'
  ctx = canvas.getContext('2d')
  ctx.scale(dpr, dpr)
  ctx.lineCap = 'round'
  ctx.lineJoin = 'round'
  // 흰 배경(투명 PNG 대신 카드에 어울리게).
  ctx.fillStyle = '#ffffff'
  ctx.fillRect(0, 0, CANVAS_W, CANVAS_H)
}

function pos(e) {
  const rect = canvasRef.value.getBoundingClientRect()
  return { x: e.clientX - rect.left, y: e.clientY - rect.top }
}

function start(e) {
  drawing = true
  canvasRef.value.setPointerCapture(e.pointerId)
  const { x, y } = pos(e)
  ctx.beginPath()
  ctx.moveTo(x, y)
  // 점 하나만 찍어도 보이도록 즉시 한 번 그린다.
  drawLineTo(x, y)
}

function move(e) {
  if (!drawing) return
  const { x, y } = pos(e)
  drawLineTo(x, y)
}

function drawLineTo(x, y) {
  ctx.strokeStyle = isEraser.value ? '#ffffff' : color.value
  ctx.lineWidth = isEraser.value ? lineWidth.value * 4 : lineWidth.value
  ctx.lineTo(x, y)
  ctx.stroke()
  ctx.beginPath()
  ctx.moveTo(x, y)
  hasDrawn.value = true
}

function end() {
  drawing = false
}

function clearAll() {
  ctx.fillStyle = '#ffffff'
  ctx.fillRect(0, 0, CANVAS_W, CANVAS_H)
  hasDrawn.value = false
}

function onSave() {
  if (!hasDrawn.value || props.saving) return
  const imageData = canvasRef.value.toDataURL('image/png')
  emit('save', { imageData, authorName: authorName.value.trim() })
}

onMounted(initCanvas)
onBeforeUnmount(() => { drawing = false })
</script>

<template>
  <div class="modal-overlay" @click.self="emit('close')">
    <div class="modal drawing-modal" data-testid="drawing-modal">
      <button class="close ghost" @click="emit('close')" aria-label="닫기">✕</button>
      <h3 class="dm-title">방명록 남기기</h3>

      <div class="dm-canvas-wrap">
        <canvas
          ref="canvasRef"
          class="dm-canvas"
          data-testid="drawing-canvas"
          @pointerdown="start"
          @pointermove="move"
          @pointerup="end"
          @pointercancel="end"
          @pointerleave="end"
        ></canvas>
      </div>

      <div class="dm-tools">
        <div class="dm-colors">
          <button
            v-for="c in PALETTE"
            :key="c"
            class="dm-swatch"
            :class="{ active: !isEraser && color === c }"
            :style="{ background: c }"
            :aria-label="`색상 ${c}`"
            @click="color = c; isEraser = false"
          ></button>
          <button
            class="dm-swatch eraser"
            :class="{ active: isEraser }"
            aria-label="지우개"
            @click="isEraser = true"
          >⌫</button>
        </div>
        <input
          class="dm-range"
          type="range" min="2" max="16" step="1"
          v-model.number="lineWidth"
          aria-label="굵기"
        />
      </div>

      <input
        class="dm-author"
        v-model="authorName"
        maxlength="30"
        placeholder="이름 (선택)"
        data-testid="author-input"
      />

      <div class="dm-actions">
        <button class="ghost" @click="clearAll" data-testid="btn-clear">전체 지우기</button>
        <button
          class="primary dm-save"
          :disabled="!hasDrawn || saving"
          @click="onSave"
          data-testid="btn-save-guestbook"
        >{{ saving ? '저장 중…' : '저장' }}</button>
      </div>
    </div>
  </div>
</template>
