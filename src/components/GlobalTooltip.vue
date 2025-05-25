<template>
    <ToolTip :x="x" :y="y" :data="data" :align="align" :max-width="500"></ToolTip>
</template>

<script setup>
    import { useTooltip } from '@/store/tooltip';
    import { storeToRefs } from 'pinia';
    import ToolTip from './ToolTip.vue';

    const tt = useTooltip();

    const { x, y, data, align } = storeToRefs(tt);

</script>
