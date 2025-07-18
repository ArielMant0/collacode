<template>
    <SidePanel v-model="model" title="Crowd-Based Warnings">
        <template #text>
            <div style="max-width: 100%;">
                <v-data-table
                    :items="warnings"
                    :headers="headers"
                    multi-sort
                    class="text-caption"
                    density="compact">

                    <template v-slot:item.type="{ item }">
                        <v-icon
                            :color="getActionColor(item.type === 1 ? OBJECTION_ACTIONS.REMOVE : OBJECTION_ACTIONS.ADD)"
                            :icon="getActionIcon(item.type === 1 ? OBJECTION_ACTIONS.REMOVE : OBJECTION_ACTIONS.ADD)"/>
                    </template>

                    <template v-slot:item.severity="{ item }">
                        <v-icon
                            icon="mdi-bell"
                            :color="item.severity === 1 ? GR_COLOR.YELLOW : GR_COLOR.RED"/>
                    </template>

                    <template v-slot:item.evidence="{ item }">
                        <td>
                            <EvidenceDot v-for="e in evidence[item.index]" :evidence="e"/>
                        </td>
                    </template>

                </v-data-table>
            </div>
        </template>
    </SidePanel>
</template>

<script setup>
    import DM from '@/use/data-manager';
    import { onMounted, ref, watch } from 'vue';
    import SidePanel from '../dialogs/SidePanel.vue';
    import { getActionColor, getActionIcon, OBJECTION_ACTIONS } from '@/store/app';
    import { GR_COLOR } from '@/store/games';
    import EvidenceDot from '../evidence/EvidenceDot.vue';

    const model = defineModel()
    const props = defineProps({
        item: { type: Object, required: false },
        itemId: { type: Number, required: false },
    })

    const evidence = ref([])
    const warnings = ref([])

    const headers = [
        { title: "Tag Name", key: "tag_name" },
        { title: "Severity", key: "severity" },
        { title: "Type", key: "type" },
        { title: "Value", key: "value" },
        { title: "Evidence", key: "evidence" },
        { title: "Explanation", key: "explanation", sortable: false },
    ]

    async function read() {

        let obj;
        if (props.item) {
            obj = props.item
        } else if (props.itemId) {
            obj = DM.getDataItem("items", props.itemId)
        }

        if (obj) {
            obj.warnings.forEach((d, i) => d.index = i)
            evidence.value = obj.warnings.map(d => obj.evidence.filter(e => e.tag_id === d.tag_id))
            warnings.value = obj.warnings
        } else {
            evidence.value = []
            warnings.value = []
        }
    }

    onMounted(read)

    watch(() => props.itemId, read)
    watch(() => props.item, read)

</script>
