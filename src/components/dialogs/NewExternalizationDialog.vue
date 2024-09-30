<template>
    <MiniDialog v-model="model" title="Add new externalization" @cancel="cancel" @submit="save" min-width="1000">
        <template v-slot:text>
            <div class="d-flex">
                <div style="width: 40%;">
                    <v-text-field :model-value="item.name"
                        readonly
                        disabled
                        density="compact"
                        label="Game title"
                        hide-details
                        hide-spin-buttons/>
                    <v-text-field :model-value="app.activeUser.name"
                        readonly
                        disabled
                        density="compact"
                        label="Created by"
                        hide-details
                        hide-spin-buttons/>
                    <v-textarea v-model="desc"
                        class="mt-2"
                        density="compact"
                        label="Description"
                        rows="10"
                        hide-details
                        hide-spin-buttons/>
                </div>
                <div style="width: 30%;">
                    <v-list
                        density="compact"
                        width="100%"
                        class="mt-2 mb-2">
                        <v-list-item v-for="t in item.allTags"
                            :key="'t_'+t.id"
                            :tile="t.name"
                            :subtitle="t.description"
                            :color="selected.has(t.id) ? 'bg-grey-lighten-3' : 'default'"
                            @click="toggle(t.id)"
                            />
                    </v-list>
                </div>
                <div class="d-flex flex-wrap" style="width: 30%;">
                    <EvidenceCell v-for="e in evidence"
                        class="pa-1 mr-2"
                        :key="'ev_t_'+e.id"
                        :item="e"
                        :allowed-tags="item.allTags"
                        :width="150"
                        :height="150"
                        :selected="false"/>
                </div>
            </div>
        </template>
    </MiniDialog>
</template>

<script setup>
    import { reactive, ref } from 'vue';
    import { useApp } from '@/store/app';
    import { useToast } from 'vue-toastification';
    import MiniDialog from '../dialogs/MiniDialog.vue';
    import DM from '@/use/data-manager';
import EvidenceCell from '../evidence/EvidenceCell.vue';

    const model = defineModel();
    const props = defineProps({
        item: {
            type: Object,
        },
        tag: {
            type: Number,
        },
    })

    const emit = defineEmits(["cancel", "submit"])

    const app = useApp();
    const toast = useToast();

    const desc = ref("")
    const selected = reactive(new Set())
    const evidence = computed(() => {
        const tags = props.item.allTags.filter(d => selected.has(d.id))
        if (tags.length === 0) {
            evidence.value = [];
        } else {
            const evs = DM.getDataBy("evidence", d => d.game_id === props.item.id && selected.has(d.tag_id))
            evs.forEach(e => {
                e.rows = 2 + (e.description.includes('\n') ? e.description.match(/\n/g).length : 0)
                e.open = false;
            });
            evidence.value = evs;
        }
    })

    function toggle(id){
        if (selected.has(id)) {
            selected.delete(id)
        } else {
            selected.add(id)
        }
    }

    function cancel() {
        emit("cancel")
        model.value = false;
    }
    function save() {
        emit("save")
        model.value = false;
    }
</script>