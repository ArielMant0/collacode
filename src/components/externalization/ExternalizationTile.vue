<template>
    <div ref="wrapper" class="d-flex" style="max-width: 100%;">
        <div v-if="allowEdit" class="d-flex flex-column mr-2">
            <v-btn @click="deleteItem"
                height="55"
                class="mb-1"
                density="comfortable"
                variant="outlined"
                color="error"
                rounded="0"
                size="small"
                icon="mdi-delete"/>

            <v-btn @click="emit('edit', item)"
                height="55"
                class="mt-1"
                density="comfortable"
                variant="outlined"
                color="primary"
                rounded="0"
                size="small"
                icon="mdi-pencil"/>
        </div>

        <v-sheet class="mr-2 pa-2" style="width: 30%;" color="grey-lighten-4" rounded="sm">
            <div>
                <i><b>{{ item.name }}</b></i>
                <span style="float: right;" class="text-caption">{{ item.tags.length }} tags</span>
            </div>
            <p>{{ item.description }}</p>
        </v-sheet>

        <TreeMap
            :data="allCats"
            :selected="selectedCats"
            hide-headers
            :width="wrapSize.width.value*0.3"
            :height="120"/>

        <div class="d-flex flex-wrap ml-2" style="width: 35%;">
            <EvidenceCell v-for="e in evidence"
                :key="'e_'+e.id"
                :item="e"
                :allowed-tags="tags"
                @select="app.setShowEvidence(e.id)"/>
        </div>
    </div>
</template>

<script setup>
    import DM from '@/use/data-manager';
    import { computed } from 'vue';
    import TreeMap from '../vis/TreeMap.vue';
    import { deleteExternalization } from '@/use/utility';
    import { useTimes } from '@/store/times';
    import { useToast } from 'vue-toastification';
    import { useElementSize } from '@vueuse/core';
    import EvidenceCell from '../evidence/EvidenceCell.vue';
    import { useApp } from '@/store/app';

    const props = defineProps({
        item: {
            type: Object,
            required: true
        },
        buttonLabel: {
            type: String,
            default: "select"
        },
        allowEdit: {
            type: Boolean,
            default: false
        }
    })
    const emit = defineEmits(["edit"])

    const app = useApp();
    const times = useTimes();
    const toast = useToast();
    const wrapper = ref(null)

    const wrapSize = useElementSize(wrapper)

    const allCats = computed(() => DM.getData("ext_categories"))
    const selectedCats = computed(() => props.item.categories.map(d => d.cat_id))

    const tags = computed(() => {
        const game = DM.getDataItem("games", props.item.game_id)
        return game ? game.allTags : [];
    });
    const evidence = computed(() => {
        const evs = DM.getDataBy("evidence", d => {
            return d.game_id === props.item.game_id &&
                props.item.tags.find(t => t.tag_id === d.tag_id)
        });

        evs.forEach(e => {
            e.rows = 2 + (e.description.includes('\n') ? e.description.match(/\n/g).length : 0)
            e.open = false;
        });

        evs.sort((a, b) => {
            const nameA = tags.value.find(d => d.id === a.tag_id).name.toLowerCase(); // ignore upper and lowercase
            const nameB = tags.value.find(d => d.id === b.tag_id).name.toLowerCase(); // ignore upper and lowercase
            if (nameA < nameB) { return -1; }
            if (nameA > nameB) { return 1; }
            // names must be equal
            return 0;
        })

        return evs;
    });

    async function deleteItem() {
        try {
            await deleteExternalization(props.item.id)
            toast.success("deleted 1 externalization")
            times.needsReload("externalizations")
        } catch {
            toast.error("error deleting externalization")
        }
    }

</script>