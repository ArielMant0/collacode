<template>
    <v-sheet class="pa-1" border rounded="sm">
        <div class="text-caption">
            <v-btn icon="mdi-plus" size="sm" rounded="sm" color="secondary" class="mr-1" @click="makeNew"/>
            <i>add externalization to this group</i>
        </div>
        <v-sheet v-for="e in exts" :key="e.id+'_'+time" style="width: 100%;" class="ext-bordered pa-1 mt-2">
            <ExternalizationTile :item="e" @edit="select" allow-edit show-bars/>
        </v-sheet>
    </v-sheet>
</template>

<script setup>
    import DM from '@/use/data-manager';
    import ExternalizationTile from './ExternalizationTile.vue';
    import { useApp } from '@/store/app';
    import { onMounted, ref, watch } from 'vue';
    import { useTimes } from '@/store/times';

    const props = defineProps({
        id: {
            type: Number,
            required: true
        },
        item: {
            type: Object,
            required: true
        },
    })

    const app = useApp()
    const times = useTimes()

    const time = ref(Date.now())
    const exts = ref([])

    function makeNew() {
        app.setAddExternalization(props.item.id, props.id)
    }

    function select(ext) {
        app.setShowExtGroup(props.id, ext ? ext.id : null)
    }

    function getExts() {
        if (!app.currentCode) return []
        const array = DM.getDataBy("externalizations", d => d.group_id === props.id)
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

    onMounted(function() {
        exts.value = getExts();
        time.value = Date.now();
    })

    watch(() => ([times.tags, times.datatags]), () => time.value = Date.now(), { deep: true });
    watch(() => ([times.externalizations, times.ext_agreements]), function() {
        exts.value = getExts()
        time.value = Date.now()
    }, { deep: true });

</script>
