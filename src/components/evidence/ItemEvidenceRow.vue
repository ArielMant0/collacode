<template>
    <div class="mr-2 d-flex">
        <div v-if="selected" class="d-flex flex-column align-center justify-center mr-1">
            <v-btn
                :disabled="!allowMoveUp"
                density="compact"
                rounded="sm"
                variant="text"
                icon="mdi-chevron-up"
                @click.stop="emit('move-up', item.id)"/>
            <v-btn
                :disabled="!allowMoveDown"
                density="compact"
                rounded="sm"
                variant="text"
                icon="mdi-chevron-down"
                @click.stop="emit('move-down', item.id)"/>
        </div>
        <div>
            <div class="text-caption text-dots" :style="{ 'max-width': width+'px' }" :title="item.name">
                <i>{{ item.name }}</i>
            </div>
            <v-img
                :src="item.teaser ? APP_URLS.TEASER+item.teaser : imgUrlS"
                cover
                @click.stop="emit('select', item.id)"
                class="cursor-pointer"
                :width="width"
                :height="height"></v-img>
        </div>
    </div>

    <div class="d-flex flex-wrap">
        <v-sheet v-for="e in evidence" :key="'ev_t_'+e.id" class="pa-1 mr-2" :width="height">

            <EvidenceCell
                :item="e"
                :width="width"
                :height="height"
                @select="app.setShowEvidence(e.id)"/>

        </v-sheet>

        <v-btn v-if="allowAdd"
            class="pa-2 ma-1"
            color="secondary"
            :width="height"
            :height="height"
            rounded="sm"
            icon="mdi-plus"
            @click="addEvidence"/>
    </div>

</template>

<script setup>

    import { APP_URLS, useApp } from '@/store/app';
    import EvidenceCell from '@/components/evidence/EvidenceCell.vue'

    import imgUrlS from '@/assets/__placeholder__s.png'

    const props = defineProps({
        item: {
            type: Object,
            required: true
        },
        evidence: {
            type: Array,
            default: () => ([])
        },
        selected: {
            type: Boolean,
            default: false
        },
        allowMoveUp: {
            type: Boolean,
            default: false
        },
        allowMoveDown: {
            type: Boolean,
            default: false
        },
        allowEdit: {
            type: Boolean,
            default: false
        },
        allowAdd: {
            type: Boolean,
            default: false
        },
        width: {
            type: Number,
            default: 150
        },
        height: {
            type: Number,
            default: 80
        },
        scaleFactor: {
            type: Number,
            default: 4
        },
    })
    const emit = defineEmits(["move-down", "move-up", "evidence", "select", "enlarge", "update"])

    const app = useApp();

    function addEvidence() {
        if (!props.allowAdd) return;
        app.setAddEvidence(props.item.id)
    }

</script>

<style scoped>
.text-dots {
    overflow: hidden;
    white-space: nowrap;
    text-overflow: ellipsis
}
.tiny-font {
    font-size: 10px;
    max-height: 200px;
}
</style>