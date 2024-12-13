<template>
    <div>
        group
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
    const selData = ref([])

    function resetSelection() {
        DM.removeFilter("tags_old", "id")
        app.selectByTag()
    }

    function update() {
        let p = null;
        let minDepth = Number.MAX_SAFE_INTEGER;
        selData.value = DM.getData("tags", true)
        selData.value.forEach(d => {
            if (d.parent && d.path.length - 1 < minDepth) {
                minDepth = d.path.length - 1;
                p = d.parent;
            }
        })
        tagNames.parent = p;
    }

    async function group() {
        if (!allowEdit.value) return;
        const allTags = DM.getData("tags", false)

        if (selData.value.length > 0) {

            if (!tagNames.name) {
                toast.error("missing new tag name")
                return;
            }
            if (!tagNames.desc) {
                toast.error("missing new tag description")
                return;
            }
            if (allTags.some(d => d.name === tagNames.name)) {
                toast.error("name must be unique")
                return;
            }

            const p = selData.value.find(d => d.id === tagNames.parent);
            if (p) {
                if (p.parent && !selData.value.find(d => d.id === p.parent)) {
                    tagNames.parent = p.parent === -1 ? null : p.parent;
                } else {
                    tagNames.parent = null;
                }
            }

            const parent = {
                name: tagNames.name,
                description: tagNames.desc,
                code_id: newCode.value,
                created: Date.now(),
                created_by: app.activeUserId,
                is_leaf: false,
                parent: tagNames.parent,
            }

            try {
                await addTags(parent)
                app.addAction("trans", "group tags", {
                    tags: selData.value.map(d => d.id),
                    name: tagNames.name.slice(),
                });
                toast.success("added new parent tag")
                tagNames.name = "";
                tagNames.desc = "";
                tagNames.parent = null;
                times.needsReload("tagging")
            } catch {
                toast.error("error grouping tags")
            }
        }
        resetSelection();
    }

    async function addTagsToGroup(name, tags) {
        if (!allowEdit.value) return;
        if (tags.length === 0 || !name) return false;

        const allTags = DM.getData("tags", false)
        const parent = allTags.find(d => d.name === name);
        if (!parent) {
            return false;
        }

        try {
            await updateTags(tags.map(d => {
                const tag = allTags.find(t => t.id === d);
                return {
                    id: d,
                    name: tag.name,
                    description: tag.description,
                    parent: parent.id,
                    is_leaf: tag.is_leaf
                }
            }));
            toast.success(`updated ${tags.length} tags`);
            times.needsReload("tagging");
        } catch {
            toast.error(`error updating ${tags.length} tags`);
            return false;
        }
        return true
    }

    onMounted(update)

    watch(() => times.f_tags, update)

</script>