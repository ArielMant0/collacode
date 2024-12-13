<template>
    <div>
        merge
        <v-btn color="primary">apply</v-btn>
    </div>
</template>

<script setup>

    import { useSettings } from '@/store/settings';
    import { useTimes } from '@/store/times';
    import DM from '@/use/data-manager';
    import { mergeTags } from '@/use/utility';
    import { storeToRefs } from 'pinia';
    import { reactive, watch } from 'vue';
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

    async function merge() {
        if (!allowEdit.value) return;

        const allTags = DM.getData("tags", false)
        const now = Date.now();

        if (selData.value.length > 0) {

            if (!tagNames.name) {
                toast.error("missing new tag name")
                return;
            }

            if (!selData.value.some(d => d.name === tagNames.name) &&
                allTags.some(d => d.name === tagNames.name)
            ) {
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

            const obj = {
                name: tagNames.name,
                description: tagNames.desc,
                created: now,
                created_by: app.activeUserId,
                code_id: app.newCode,
                parent:  tagNames.parent,
                ids: []
            }
            selData.value.forEach(tag => obj.ids.push(tag.id))

            try {
                await mergeTags(obj)
                toast.success("merged tags into tag " + tagNames.name)
                resetSelection();
                tagNames.name = "";
                tagNames.desc = "";
                tagNames.parent = null;
                times.needsReload("tagging")
            } catch {
                toast.error("error merging tags into tag " + tagNames.name)
            }
        }
    }

    watch(() => times.f_tags, update)

</script>