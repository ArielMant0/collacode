<template>
    <v-sheet class="pa-1" border rounded style="text-align: left;">
        <div class="text-caption">
            <span>{{ name }}</span>
            <v-btn icon="mdi-plus" size="sm" rounded="sm" color="secondary" class="ml-2 mr-1" :disabled="!allowEdit"  @click="makeNew"/>
            <i>add a new externalization to this group</i>
        </div>
        <v-sheet v-for="e in exts" style="width: 100%;" class="ext-bordered pa-1 mt-2">
            <ExternalizationTile :item="e" :key="e.id+'_'+time" @edit="select" :allow-edit="allowEdit" show-bars/>
        </v-sheet>
    </v-sheet>
</template>

<script setup>
    import DM from '@/use/data-manager';
    import ExternalizationTile from './ExternalizationTile.vue';
    import { useApp } from '@/store/app';
    import { onMounted, ref, watch } from 'vue';
    import { useTimes } from '@/store/times';
    import { storeToRefs } from 'pinia';

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

    const { allowEdit } = storeToRefs(app)

    const name = ref("")
    const time = ref(Date.now())
    const exts = ref([])

    function makeNew() {
        if (!allowEdit.value) return;
        app.setAddExternalization(props.item.id, props.id)
    }

    function select(ext) {
        app.setShowExtGroup(props.id, ext ? ext.id : null)
    }

    function readName() {
        name.value = DM.getDataItem("ext_groups", props.id).name
    }
    function readExts() {
        if (!app.currentCode) return []

        readName();
        const sel = props.selected ? new Set(props.selected) : DM.getSelectedIds("externalizations")

        const array = DM.getDataBy("externalizations", d => {
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
    watch(() => Math.max(times.ext_groups, times.externalizations, times.ext_agreements), readExts);

</script>
