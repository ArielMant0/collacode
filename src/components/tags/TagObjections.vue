<template>
    <SidePanel v-model="model" width="50vw" @close="close" :title="'Objections for tag '+name">
        <template #text>
            <div class="text-caption">
                <table style="border-spacing: 4px;">
                    <tbody>
                        <tr>
                            <td>tag:</td>
                            <td><b>{{ name }}</b></td>
                        </tr>
                        <tr v-if="itemId">
                            <td>{{ app.itemName }}:</td>
                            <td><b>{{ itemName }}</b></td>
                        </tr>
                    </tbody>
                </table>
            </div>
            <div class="d-flex align-center text-caption mb-4">
                <v-checkbox-btn
                    v-model="showAllUsers"
                    color="primary"
                    density="compact"
                    inline
                    true-icon="mdi-tag"
                    false-icon="mdi-tag-off"
                    :disabled="app.static"/>

                <span class="ml-1 text-caption">objections based on {{ showAllUsers ? 'all' : 'your' }} tags</span>
            </div>

            <div style="max-height: 80vh; overflow-y: auto;" class="d-flex flex-wrap">
                <ObjectionTable v-if="tagId"
                    :tag-id="tagId"
                    :item-id="itemId"
                    :show-all="showAllUsers"
                    :exclude-headers="excludeHeaders"/>
            </div>
        </template>
    </SidePanel>
</template>

<script setup>
    import { useApp } from '@/store/app';
    import { useTimes } from '@/store/times';
    import DM from '@/use/data-manager';
    import { onMounted, watch } from 'vue';
    import ObjectionTable from '../objections/ObjectionTable.vue';
    import SidePanel from '../dialogs/SidePanel.vue';

    const app = useApp()
    const times = useTimes()

    const model = defineModel()
    const props = defineProps({
        tagId: { type: Number },
        itemId: { type: Number }
    })
    const emit = defineEmits(["close"])

    const showAllUsers = ref(app.showAllUsers)
    const name = ref("")
    const itemName = ref("")

    const excludeHeaders = ["created", "resolution"]
    function close() {
        emit("close")
    }

    function readObjections() {
        model.value = props.tagId !== undefined && props.tagId !== null
        if (!props.tagId) {
            name.value = ""
            itemName.value = ""
            return
        }

        name.value = DM.getDataItem("tags_name", props.tagId)
        itemName.value = props.itemId ?
            DM.getDataItem("items_name", props.itemId) :
            ""
    }

    onMounted(readObjections)

    watch(() => props.tagId, readObjections)
    watch(() => props.itemId, readObjections)
    watch(() => Math.max(times.datasets, times.objections), readObjections)

</script>

<style scoped>
.my-window {
    position: fixed;
    top: 50px;
    user-select: none;
    width: 32%;
    min-width: 350px;
    height: 95vh;
    z-index: 3;
}
</style>