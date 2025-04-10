<template>
  <button @click=\"handleClick\" :style=\"buttonStyle\">
    {{ buttonText }}
  </button>
</template>

<script>
export default {
  name: 'MyButton',
  props: {
    buttonText: {
      type: String,
      default: 'Click me'
    },
    buttonColor: {
      type: String,
      default: '#007bff'  
    }
  },
  computed: {
    buttonStyle() {
      return {
        backgroundColor: this.buttonColor,
        color: '#fff',
        border: 'none',
        padding: '10px 20px',
        borderRadius: '5px',
        cursor: 'pointer'
      };
    }
  },
  methods: {
    handleClick() {
      this.$emit('click');
    }
  }
};
</script>
