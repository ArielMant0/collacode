

<template>
    <div v-if="!hidden" class="d-flex flex-column align-center">
        <div class="d-flex align-center">
            <MiniTree/>
            <span style="width: 100px;" class="ml-2"></span>
        </div>
        <div class="d-flex align-center mb-1">
            <TagBarCode/>
            <span style="width: 100px; text-align: left;" class="text-caption ml-2">all games</span>
        </div>
        <div class="d-flex align-center">
            <TagBarCode :filter="d => d._selected"/>
            <span style="width: 100px; text-align: left;" class="text-caption ml-2">selection</span>
        </div>
    </div>
</template>

<script setup>
    import TagBarCode from '../tags/TagBarCode.vue';
    import MiniTree from '../vis/MiniTree.vue';

    const props = defineProps({
        hidden: {
            type: Boolean,
            default: false
        }
    })
</script>