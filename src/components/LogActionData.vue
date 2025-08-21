<template>
    <div class="text-caption">

        <div v-if="actionType === ACTION_TYPE.WARNINGS" class="d-flex align-start">

            <div v-if="data.enable_warnings !== undefined">
                {{ data.enable_warnings ? 'enable' : 'disable' }} warnings
            </div>

            <div v-if="data.item" class="mr-2">
                <div><span v-if="!data.item.finalized"><b>not</b></span> finalized</div>
                <ItemTeaser :id="data.item.id" :width="120" :height="60"/>
            </div>

            <div v-if="data.warnings" class="d-flex flex-column flex-wrap" style="max-height: 100px;">
                <div v-for="w in data.warnings" class="d-flex align-center">
                    <v-icon :color="getWarningColor(w)">mdi-circle-medium</v-icon>
                    <WarningIcon :warning="w" size="x-small" class="mr-1"/>
                    <TagText :id="w.tag_id" :item-id="data.item.id" class="mr-1"/>
                </div>
            </div>
        </div>

        <div v-else-if="actionType === ACTION_TYPE.ITEM">

            <div v-for="d in data">
                <div v-if="d.item">
                    <ItemTeaser :id="d.item.id" :width="120" :height="60"/>
                </div>
            </div>
        </div>

        <div v-else-if="actionType === ACTION_TYPE.EVIDENCE">

            <div v-for="e in data">
                <div v-if="e.item">
                    <ItemTeaser :id="e.item.id" :width="120" :height="60"/>
                </div>
                <div v-if="e.tag.id">
                    <b><TagText :id="e.tag.id"/></b>
                </div>
                <div>{{ e.description }}</div>
            </div>
        </div>

        <div v-else-if="actionType === ACTION_TYPE.DATATAG">
            <div v-for="d in data">
                <div v-if="d.item">
                    <ItemTeaser :id="d.item.id" :width="120" :height="60"/>
                </div>
                <div v-if="d.datatags" class="d-flex flex-wrap">
                    <template v-for="(dt, i) in d.datatags">
                        <span v-if="i > 0" class="pl-1 pr-1">-</span>
                        <TagText :id="dt.tag.id"/>
                    </template>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
    import { computed } from 'vue';
    import ItemTeaser from './items/ItemTeaser.vue';
    import TagText from './tags/TagText.vue';
    import WarningIcon from './warnings/WarningIcon.vue';
    import { getWarningColor } from '@/use/similarities';

    const ACTION_TYPE =  Object.freeze({
        ANY: 0,
        ITEM: 1,
        TAG: 2,
        DATATAG: 3,
        EVIDENCE: 4,
        WARNINGS: 5,
    })

    const props = defineProps({
        action: {
            type: String,
            required: true
        },
        data: {
            type: [Object, Array],
            required: true
        }
    })

    const actionType = computed(() => {
        if (props.action.includes("item")) {
            return ACTION_TYPE.ITEM
        }
        if (props.action.includes("datatag")) {
            return ACTION_TYPE.DATATAG
        }
        if (props.action.includes("tag")) {
            return ACTION_TYPE.TAG
        }
        if (props.action.includes("warning")) {
            return ACTION_TYPE.WARNINGS
        }
        if (props.action.includes("evidence")) {
            return ACTION_TYPE.EVIDENCE
        }
        return ACTION_TYPE.ANY
    })

</script>