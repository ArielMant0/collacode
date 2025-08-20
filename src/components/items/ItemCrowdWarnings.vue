<template>
    <SidePanel v-model="model" width="50vw" title="Crowd-Based Warnings">
        <template #text>
            <div style="max-width: 100%; max-height: 80vh;">
                <div v-if="hidden" style="text-align: center;">
                    permanently enable warnings to see them here
                </div>
                <v-data-table v-else
                    :items="warnings"
                    :headers="headers"
                    multi-sort
                    class="text-caption"
                    density="compact">

                    <template v-slot:item.tag_name="{ item }">
                        <TagText :id="item.tag_id"/>
                    </template>

                    <template v-slot:item.type="{ item }">
                        <v-icon
                            :color="getWarningColor(item)"
                            :icon="getActionIcon(item.type)"/>
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

                    <template v-slot:item.users="{ item }">
                        <td class="d-flex flex-wrap" style="max-width: 120px;">
                            <UserChip v-for="uid in item.users"
                                :id="uid"
                                short small
                                class="text-caption mb-1 mt-1"
                                />
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
    import { getActionColor, getActionIcon, useApp } from '@/store/app';
    import { GR_COLOR } from '@/store/games';
    import EvidenceDot from '../evidence/EvidenceDot.vue';
    import UserChip from '../UserChip.vue';
    import { useTimes } from '@/store/times';
    import TagText from '../tags/TagText.vue';
    import { getWarningColor } from '@/use/similarities';

    const app = useApp()
    const times = useTimes()

    const model = defineModel()
    const props = defineProps({
        item: { type: Object, required: false },
        itemId: { type: Number, required: false },
    })

    const evidence = ref([])
    const warnings = ref([])
    const hidden = ref(false)

    const headers = [
        { title: "Tag", key: "tag_name" },
        { title: "Severity", key: "severity" },
        { title: "Type", key: "type" },
        { title: "EV", key: "evidence", value: d => evidence.value[d.index].length },
        { title: "Users", key: "users" },
        { title: "Explanation", key: "explanation", sortable: false },
    ]

    async function read() {

        let obj;
        if (props.item) {
            obj = props.item
        } else if (props.itemId) {
            obj = DM.getDataItem("items_id", props.itemId)
        }

        readFinalized()
        if (obj && !hidden.value) {
            const match = app.showAllUsers ?
                obj.warnings :
                obj.warnings.filter(d => d.users.includes(app.activeUserId))

            match.forEach((d, i) => d.index = i)

            evidence.value = match.map(d => obj.evidence.filter(e => e.tag_id === d.tag_id))
            warnings.value = match
        } else {
            evidence.value = []
            warnings.value = []
        }
    }

    function readFinalized() {
        const id = props.item ? props.item.id : props.itemId
        hidden.value = id ? !DM.getDataItem("items_finalized", id) : true
    }

    onMounted(read)

    watch(() => props.itemId, read)
    watch(() => props.item, read)
    watch(() => times.items_finalized, read)

</script>
