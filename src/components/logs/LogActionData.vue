<template>
    <div class="text-caption">

        <div v-if="actionType === ACTION_TYPE.WARNINGS" class="d-flex align-start">

            <div v-if="data.enable_warnings !== undefined" class="d-flex align-center">
                <v-icon
                    class="mr-1"
                    :icon="data.enable_warnings ? 'mdi-radiobox-marked' : 'mdi-radiobox-blank'"
                    />
                warnings {{ data.enable_warnings ? 'on' : 'off' }}
            </div>

            <div v-if="data.item" class="mr-2">
                <div class="d-flex align-center" style="margin-bottom: 1px;">
                    <v-icon
                        class="mr-1"
                        :icon="data.item.finalized ? 'mdi-radiobox-marked' : 'mdi-radiobox-blank'"
                        />
                    <span style="vertical-align: middle;">finalized</span>
                </div>
                <ItemTeaser :id="data.item.id" :width="120" :height="60"/>
            </div>

            <div v-if="data.warnings" class="d-flex flex-column flex-wrap" style="max-height: 100px;">
                <div v-for="w in data.warnings" class="d-flex align-center">
                    <v-icon
                        size="small"
                        :color="getWarningColorByType(w.type)"
                        :icon="w.active ? 'mdi-radiobox-marked' : 'mdi-radiobox-blank'"
                        />
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
            <LogEntryEvidence :data="data"/>
        </div>

        <div v-else-if="actionType === ACTION_TYPE.DATATAG">
            <div v-for="d in data">
                <div v-if="d.item">
                    <ItemTeaser :id="d.item.id" :width="120" :height="60"/>
                </div>
                <div v-if="d.datatags" class="d-flex flex-wrap">
                    <span v-for="(dt, i) in d.datatags">
                        <span v-if="i > 0" class="pl-1 pr-1">-</span>
                        <TagText :id="dt.tag.id"/>
                    </span>
                </div>
            </div>
        </div>

        <div v-else-if="actionType === ACTION_TYPE.OBJECTION">
            <div v-for="d in data" class="d-flex">
                <ItemTeaser v-if="d.item_id" :id="d.item_id" :width="120" :height="60"/>
                <div class="ml-3">
                    <div class="d-flex">
                        <ObjectionStatusIcon :status="d.status"/>
                        <ObjectionIcon :action="d.action" class="mr-1"/>
                        <b v-if="d.tag_id"><TagText :id="d.tag_id"/></b>
                    </div>
                    <p><b>Explanation:</b> {{ d.explanation }}</p>
                    <div v-if="d.resolved">
                        <UserChip :id="d.resolved_by" small short/>
                        <p><b>Resolution:</b> {{ d.resolution }}</p>
                    </div>
                </div>
            </div>
        </div>

        <div v-else>
            <LogEntryAny :data="data"/>
        </div>
    </div>
</template>

<script setup>
    import ItemTeaser from '@/components/items/ItemTeaser.vue';
    import TagText from '@/components/tags/TagText.vue';
    import WarningIcon from '@/components/warnings/WarningIcon.vue';
    import { getWarningColorByType } from '@/use/similarities';
    import { ACTION_TYPE } from '@/use/log-utils';
    import LogEntryAny from './LogEntryAny.vue';
    import ObjectionIcon from '../objections/ObjectionIcon.vue';
    import ObjectionStatusIcon from '../objections/ObjectionStatusIcon.vue';
    import UserChip from '../UserChip.vue';
    import { computed, onMounted } from 'vue';
    import DM from '@/use/data-manager';
    import { useApp } from '@/store/app';
    import LogEntryEvidence from './LogEntryEvidence.vue';

    const app = useApp()

    const props = defineProps({
        actionType: {
            type: Number,
            required: true
        },
        data: {
            type: [Object, Array],
            required: true
        }
    })

    const evidence = ref({})
    const many = computed(() => Array.isArray(props.data))

    function read() {
        if (props.actionType === ACTION_TYPE.EVIDENCE) {

            const ids = new Set()
            if (Array.isArray(props.data)) {
                props.data.forEach(d => d.id ? ids.add(d.id) : null)
            } else if (props.data.id) {
                ids.add(props.data.id)
            }

            const evs = DM.getDataBy("evidence", d => ids.has(d.id))
            const obj = {}
            evs.forEach(d => obj[d.id] = d)
            evidence.value = obj
        }
    }

    onMounted(read)

</script>