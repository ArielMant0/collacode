<template>
    <div style="text-align: left;">
        <v-number-input v-model="numChildren"
            label="number of children"
            :min="2"
            :step="1"
            class="mb-1"
            control-variant="stacked"
            density="compact"
            @update:model-value="checkChildNames"
            hide-details
            hide-spin-buttons/>
        <v-btn color="secondary" block density="compact" @click="split">split</v-btn>
        <div v-if="tag" class="mt-2 ml-2 text-caption">
            <div v-if="tag.parentName">{{ tag.parentName }}</div>
            <div class="ml-4" style="text-decoration: line-through;">{{ tag.name }}</div>
            <div v-for="i in numChildren" class="ml-8" style="width: 100%;">
                <input v-model="tagNames[i-1]" type="text" style="font-style: italic; width: 85%;" :placeholder="'tag '+i"/>
            </div>
        </div>
    </div>
</template>

<script setup>

    import { useApp } from '@/store/app';
    import { useSettings } from '@/store/settings';
    import { useTimes } from '@/store/times';
    import DM from '@/use/data-manager';
    import { splitTags } from '@/use/utility';
    import { range } from 'd3';
    import { storeToRefs } from 'pinia';
    import { ref, onMounted, watch } from 'vue';
    import { useToast } from 'vue-toastification';

    const app = useApp()
    const toast = useToast()
    const times = useTimes()
    const settings = useSettings()

    const { allowEdit } = storeToRefs(app)

    const tagNames = reactive({})
    const numChildren = ref(2)

    const tag = ref(null)

    function resetSelection() {
        DM.removeFilter("tags_old", "id")
        app.selectByTag()
    }

    function checkChildNames(reset=false) {
        const options = range(0, numChildren.value)
        options.forEach(o => {
            if (!tagNames[o] || reset === true) {
                tagNames[o] = "tag " + (o + 1)
            }
        })
    }

    function update() {
        const selData = DM.getData("tags", true)
        if (selData.length === 0) {
            tag.value = null;
            checkChildNames(true)
        } else if (tag.value === null || selData[0].id !== tag.value.id) {
            tag.value = selData[0]
            tag.value.parentName = tag.value.parent ? DM.getDataItem("tags_name", tag.value.parent) : null
            checkChildNames(true)
        }
    }

    async function split() {
        if (!allowEdit.value) return;
        const num = numChildren.value;
        const now = Date.now();

        if (num > 0 && tag.value !== null) {

            const names = [];
            const nameSet = new Set(DM.getData("tags_name").values())
            for (let i = 0; i < num; ++i) {
                if (nameSet.has(tagNames[i])) {
                    return toast.error(`name ${tagNames[i]} already exists`)
                }
                names.push(tagNames[i])
            }

            try {
                await splitTags([{
                    id: tag.value.id,
                    names: names,
                    created_by: app.activeUserId,
                    created: now
                }])
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