<template>
    <v-sheet class="pa-1" border rounded style="text-align: left;">
        <div class="text-caption d-flex align-center">
            <span>{{ name }}</span>
            <v-btn icon="mdi-plus" variant="tonal" size="sm" rounded="sm" color="primary" class="ml-2 mr-1" @click="makeNew"/>
            <i>add a new {{ app.metaItemName }} to this group</i>
        </div>
        <v-sheet v-for="e in exts" style="width: 100%;" class="ext-bordered pa-1 mt-2">
            <MetaItemTile :item="e" :key="e.id+'_'+time" @edit="select" show-bars/>
        </v-sheet>
    </v-sheet>
</template>

<script setup>
    import DM from '@/use/data-manager';
    import MetaItemTile from './MetaItemTile.vue';
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
        selected: {
            type: Array,
            required: false
        },
    })

    const app = useApp()
    const times = useTimes()

    const name = ref("")
    const time = ref(Date.now())
    const exts = ref([])

    function makeNew() {
        app.setAddMetaItem(props.item.id, props.id)
    }

    function select(ext) {
        app.setShowMetaGroup(props.id, ext ? ext.id : null)
    }

    function readName() {
        name.value = DM.getDataItem("meta_groups", props.id).name
    }
    function readExts() {
        if (!app.currentCode) return []

        readName();
        const sel = props.selected ? new Set(props.selected) : DM.getSelectedIds("meta_items")

        const array = DM.getDataBy("meta_items", d => {
            return d.group_id === props.id && (sel.size === 0 || sel.has(d.id))
        })

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
        exts.value = array
        time.value = Date.now();
    }

    onMounted(function() {
        readName()
        readExts()
    })

    watch(() => props.id, readName)
    watch(() => props.selected, readExts);
    watch(() => Math.max(times.tags, times.datatags), () => time.value = Date.now());
    watch(() => Math.max(times.meta_groups, times.meta_items, times.meta_agreements), readExts);

</script>
