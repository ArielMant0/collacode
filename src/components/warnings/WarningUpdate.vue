<template>
    <div>
        <div v-if="countAdded === 0 && countRemoved === 0">no warning changes</div>
        <div v-if="countRemoved > 0">{{ countRemoved }} warning{{ countRemoved > 1 ? '(s)' : '' }} removed</div>
        <div v-if="countAdded > 0">{{ countAdded }} warning{{ countAdded > 1 ? '(s)' : '' }}  added</div>
    </div>
</template>

<script setup>

    const props = defineProps({
        countAdded: {
            type: Number,
            default: 0
        },
        countRemoved: {
            type: Number,
            default: 0
        }
    })
</script>