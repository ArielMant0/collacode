<template>
    <div class="d-flex align-start">
        <div style="width: 100%">
            <div style="text-align: center;" class="mb-4">
                <p class="text-caption mb-1"><i>externalizations are actions that create or modify visual representations to replace mental simulation or reduce mental load</i></p>
                <v-btn
                    color="secondary"
                    rounded="sm"
                    prepend-icon="mdi-plus"
                    @click="makeNew">
                    add new externalization
                </v-btn>
            </div>
            <v-sheet v-for="e in exts" :key="e.id+'_'+time" style="width: 100%;" class="ext-bordered pa-1 mt-2">
                <ExternalizationTile :item="e" @edit="select" allow-edit/>
            </v-sheet>
        </div>
    </div>
</template>

<script setup>
    import DM from '@/use/data-manager';
    import ExternalizationTile from './ExternalizationTile.vue';
    import { useApp } from '@/store/app';
    import { ref, watch } from 'vue';
    import { useTimes } from '@/store/times';

    const props = defineProps({
        item: {
            type: Object,
            required: true
        }
    })

    const app = useApp()
    const times = useTimes()

    const time = ref(Date.now())
    const exts = ref(getExts())

    function select(ext) {
        app.setShowExternalization(ext ? ext.id : null)
    }
    function makeNew() {
        app.setAddExternalization(props.item.id)
    }
    function getExts() {
        if (!app.currentCode) return []
        const array = DM.getDataBy("externalizations", d => d.game_id === props.item.id && d.code_id === app.currentCode)
        array.forEach(e => {
            e.tags.sort((a, b) => {
                if (!a.tag_id || !b.tag_id) return 0;
                const nameA = props.item.allTags.find(d => d.id === a.tag_id).name.toLowerCase();
                const nameB = props.item.allTags.find(d => d.id === b.tag_id).name.toLowerCase();
                if (nameA < nameB) { return -1; }
                if (nameA > nameB) { return 1; }
                // names must be equal
                return 0;
            });
        })
        return array
    }

    watch(() => [times.tags, times.datatags, times.externalizations, times.ext_agreements], function() {
        exts.value = getExts()
        time.value = Date.now()
    }, { deep: true });

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