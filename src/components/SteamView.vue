<template>
    <div>
        <iframe :width="width" :height="height" :src="data.url"/>
    </div>
</template>

<script setup>
    const props = defineProps({
        data: {
            type: Object,
            required: true
        },
        width: {
            type: Number,
            default: 600
        },
        height: {
            type: Number,
            default: 600
        },
    })
</script>