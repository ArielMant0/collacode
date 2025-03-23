<template>
    <div class="d-flex align-start">
        <div style="width: 100%">
            <v-btn v-if="allowEdit"
                color="secondary"
                rounded="sm"
                block
                class="mb-4 text-caption"
                prepend-icon="mdi-plus"
                @click="makeNew">
                add new {{ app.metaItemName }}
            </v-btn>
            <div style="max-height: 85vh; overflow-y: auto;">
                <MetaGroupTile v-for="g in groups"
                    :id="g.id" :key="g.id"
                    :item="item"
                    class="mb-1"/>
            </div>
        </div>
    </div>
</template>

<script setup>
    import DM from '@/use/data-manager';
    import { useApp } from '@/store/app';
    import { onMounted, ref, watch } from 'vue';
    import { useTimes } from '@/store/times';
    import MetaGroupTile from './MetaGroupTile.vue';
    import { storeToRefs } from 'pinia';

    const props = defineProps({
        item: {
            type: Object,
            required: true
        }
    })

    const app = useApp()
    const times = useTimes()

    const { allowEdit } = storeToRefs(app)

    const groups = ref([])

    function makeNew() {
        app.setAddMetaItem(props.item.id)
    }
    function getGroups() {
        if (!app.currentCode) return []
        groups.value = DM.getDataBy("meta_groups", d => d.item_id === props.item.id && d.code_id === app.currentCode)
    }

    onMounted(getGroups)

    watch(() => Math.max(times.meta_groups, times.meta_items), getGroups);

</script>