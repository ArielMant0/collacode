<template>
    <div class="d-flex align-start">
        <div style="width: 100%">
            <div class="mb-4 text-caption">
                <div v-if="allowEdit" style="text-align: center;">
                    <v-btn
                        color="secondary"
                        rounded="sm"
                        class="text-caption"
                        prepend-icon="mdi-plus"
                        @click="makeNew">
                        add new {{ app.schemeMetaItemName }}
                    </v-btn>
                </div>
            </div>
            <MetaGroupTile v-for="g in groups"
                :id="g.id" :key="g.id"
                :item="item"
                :allow-edit="allowEdit"
                class="mb-1"/>
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