<template>
  <div>
    <button @click="showAlert">버튼</button>
  </div>
</template>

<script>
export default {
  methods: {
    showAlert() {
      alert('123');
    }
  }
}
</script>
