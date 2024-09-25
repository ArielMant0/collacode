<template>
    <v-sheet class="pa-1" :style="{ position: 'absolute', top: top+'px', left: left+'px'}" border>
        <div class="d-flex flex-column text-caption">
            <div v-for="o in options" class="cursor-pointer pl-1 pr-1 onhover" @click="select(o)">{{ o }}</div>
            <div class="mt-2 pl-1 pr-1 cursor-pointer onhover" @click="close"><i>cancel</i></div>
        </div>
    </v-sheet>
</template>

<script setup>
    const props = defineProps({
        options: {
            type: Array,
            required: true
        },
        top: {
            type: Number,
            required: true
        },
        left: {
            type: Number,
            required: true
        },
    });

    const emit = defineEmits(["select", "cancel"])

    function select(option) { emit("select", option) }
    function close() { emit("cancel") }
</script>

<style scoped>
.onhover:hover {
    background-color: lightgrey;
}
</style>