<template>
    <ToolTip :x="eX" :y="eY" :data="evidence" align="right">
        <template v-slot:default>
            <EvidenceCell :item="evidenceData" :height="200" image-fit show-desc autoplay/>
        </template>
    </ToolTip>
</template>

<script setup>
    import { useTooltip } from '@/store/tooltip';
    import ToolTip from '../ToolTip.vue';
    import EvidenceCell from './EvidenceCell.vue';
    import { storeToRefs } from 'pinia';

    const tt = useTooltip()
    const { evidence, evidenceData, eX, eY } = storeToRefs(tt)
</script>