<template>
    <div>
        add
        <v-btn color="primary">apply</v-btn>
    </div>
</template>

<script setup>

    import { useSettings } from '@/store/settings';
    import { useTimes } from '@/store/times';
    import DM from '@/use/data-manager';
    import { addTags } from '@/use/utility';
    import { storeToRefs } from 'pinia';
import { onMounted, watch } from 'vue';
    import { useToast } from 'vue-toastification';

    const toast = useToast()
    const times = useTimes()
    const settings = useSettings()

    const { allowEdit } = storeToRefs(settings)

    const tagNames = reactive({})
    const numChildren = ref(1)

    const selData = ref([])

    function resetSelection() {
        DM.removeFilter("tags_old", "id")
        app.selectByTag()
    }

    function update() {
        selData.value = DM.getData("tags", true)
    }

    async function add() {
        if (!allowEdit.value) return;
        const allTags = DM.getData("tags", false)

        const num = Number.parseInt(numChildren.value);
        const rows = [];
        const now = Date.now();

        if (num > 0) {
            // add to root
            if (selData.value.length === 0) {
                for (let i = 0; i < num; ++i) {
                    rows.push({
                        name: tagNames[(i+1)] ? tagNames[(i+1)] : "new tag "+(i+1),
                        description: "",
                        code_id: props.newCode,
                        parent: null,
                        is_leaf: true,
                        created: now,
                        created_by: app.activeUserId
                    })
                }
            } else {
                const tag = selData.value[0]
                const name = tag.name;
                for (let i = 0; i < num; ++i) {
                    rows.push({
                        name: tagNames[(i+1)] ? tagNames[(i+1)] : name+" child "+(i+1),
                        description: "",
                        code_id: props.newCode,
                        parent: tag.id,
                        is_leaf: true,
                        created: now,
                        created_by: app.activeUserId
                    })
                }
            }

            const nameSet = new Set(rows.map(d => d.name))
            if (nameSet.size < rows.length || allTags.some(d => nameSet.has(d.name))) {
                toast.error("names must be unique")
                return;
            }

            try {
                await addTags(rows)
                toast.success("created " + rows.length + " children")
                resetSelection();
                times.needsReload("tags")
            } catch {
                toast.error("error creating " + rows.length + " children")
            }
        }
    }

    onMounted(update)

    watch(() => times.f_tags, update)

</script>