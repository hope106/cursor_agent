<template>
  <div class=\"hello\">
    <h1>{{ msg }}</h1>
  </div>
</template>

<script>
export default {
  name: 'HelloWorld',
  data() {
    return {
      msg: 'Hello 5 Minute Coding!'
    }
  }
}
</script>

<style scoped>
h1 {
  font-size: 2em;
  color: #42b983;
}
</style>
