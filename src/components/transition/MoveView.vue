<template>
    <div>
        move
        <v-btn color="primary">apply</v-btn>
    </div>
</template>

<script setup>

    import { useSettings } from '@/store/settings';
    import { useTimes } from '@/store/times';
    import DM from '@/use/data-manager';
    import { updateTags } from '@/use/utility';
    import { storeToRefs } from 'pinia';
    import { useToast } from 'vue-toastification';

    const toast = useToast()
    const times = useTimes()
    const settings = useSettings()

    const { allowEdit } = storeToRefs(settings)

    function resetSelection() {
        DM.removeFilter("tags_old", "id")
        app.selectByTag()
    }

    function update() {
        selData.value = DM.getData("tags", true)
    }

    async function move() {
        if (!allowEdit.value) return;
        const allTags = DM.getData("tags", false)

        if (selData.value.length > 0) {
            const vals = selData.value.map(d => d.id)
            const first = allTags.find(d => d.id === vals[0]);
            if (!first) {
                toast.error("cannot find first selected tag with id" + vals[0])
                return;
            }

            const tags = [];
            vals.forEach(d => {
                if (d === first.id) return;
                const t = allTags.find(dd => dd.id === d)
                tags.push({
                    id: t.id,
                    name: t.name,
                    description: t.description,
                    parent: first.id,
                    is_leaf: t.is_leaf
                });
            })

            try {
                await updateTags(tags)
                toast.success("updated " + tags.length + "tag(s)")
                resetSelection();
                times.needsReload("tagging")
            } catch {
                toast.error("error updating " + tags.length + "tag(s)")
            }
        }
    }

</script>