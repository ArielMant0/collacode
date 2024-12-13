<template>
    <div>
        split
        <v-btn color="primary">apply</v-btn>
    </div>
</template>

<script setup>

    import { useSettings } from '@/store/settings';
    import { useTimes } from '@/store/times';
    import DM from '@/use/data-manager';
    import { splitTags } from '@/use/utility';
    import { storeToRefs } from 'pinia';
    import { ref, onMounted, watch } from 'vue';
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

    async function split() {
        if (!allowEdit.value) return;
        const allTags = DM.getData("tags", false)

        const num = Number.parseInt(numChildren.value);
        const now = Date.now();

        if (num > 0 && selData.value.length > 0) {

            const names = [];
            const tag = selData.value[0];
            for (let i = 0; i < num; ++i) {
                names.push(tagNames[(i+1)] ? tagNames[(i+1)] : tag.name+" child "+(i+1))
            }

            const nameSet = new Set(names)
            if (nameSet.size < names.length || allTags.some(d => nameSet.has(d.name))) {
                toast.error("names must be unique")
                return;
            }

            try {
                await splitTags({ id: tag.id, names: names, created_by: app.activeUserId, created: now })
                toast.success("split tag into " + names.length + " children")
                resetSelection();
                times.needsReload("tagging")
            } catch {
                toast.error("error splitting tag")
            }
        }
    }

    onMounted(update)

    watch(() => times.f_tags, update)

</script>