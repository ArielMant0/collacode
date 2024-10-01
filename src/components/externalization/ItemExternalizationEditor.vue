<template>
    <div class="d-flex align-start" style="width: 100%">
        <div style="width: 60%;" class="mr-4">
            <v-btn class="pa-2 mr-2"
                color="secondary"
                rounded="sm"
                prepend-icon="mdi-plus"
                block
                @click="addExt = true">
                add new externalization
            </v-btn>
            <v-sheet v-for="e in exts" :key="e.id"
                :class="['ext-bordered pa-1 mt-2', selected === e.id ? 'selected' : '']">
                <ExternalizationTile :item="e" @select="select" allow-edit/>
            </v-sheet>
        </div>
        <div style="width: 40%;">
            <ExternalizationWidget v-if="selectedObj" :item="selectedObj" allow-edit/>
        </div>
        <NewExternalizationDialog v-model="addExt" :item="item"/>
    </div>
</template>

<script setup>
    import DM from '@/use/data-manager';
    import ExternalizationTile from './ExternalizationTile.vue';
    import ExternalizationWidget from './ExternalizationWidget.vue';
    import NewExternalizationDialog from '../dialogs/NewExternalizationDialog.vue';
    import { useApp } from '@/store/app';
    import { ref, computed } from 'vue';
    import { useTimes } from '@/store/times';

    const props = defineProps({
        item: {
            type: Object,
            required: true
        }
    })

    const app = useApp()
    const times = useTimes()

    const addExt = ref(false)

    const selected = ref(-1)
    const selectedObj = computed(() => {
        if (selected.value < 0) return null;
        return exts.value.find(d => d.id === selected.value)
    })

    const exts = ref(DM.getDataBy("externalizations", d => d.game_id === props.item.id && d.code_id === app.currentCode))

    function select(ext) {
        selected.value = ext ? ext.id : null
    }

    watch(() => times.externalizations, function() {
        exts.value = DM.getDataBy("externalizations", d => {
            return d.game_id === props.item.id && d.code_id === app.currentCode
        })
        // reset selected externalization if necessary (because deleted)
        if (selected.value >= 0 && ! selectedObj.value) {
            selected.value = -1;
        }
    });

</script>

<style>
.ext-bordered {
    border: 2px solid white;
    border-radius: 5px;
}
.ext-bordered.selected {
    border-color: #09c293;
}
</style>