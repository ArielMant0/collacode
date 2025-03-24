<template>
    <svg width="60" height="15" class="mr-4">
        <circle cx="7" cy="7" r="5" fill="#ffffff" class="exp-rating" stroke="black" :opacity="expRating == 0 ? 1:0.25" @click.stop="setGameExpertise(0)">
            <title>none</title>
        </circle>
        <circle cx="23" cy="7" r="5" fill="#e31a1c" class="exp-rating" stroke="black" :opacity="expRating == 1 ? 1:0.25" @click.stop="setGameExpertise(1)">
            <title>basic research</title>
        </circle>
        <circle cx="38" cy="7" r="5" fill="#e8e120" class="exp-rating" stroke="black" :opacity="expRating == 2 ? 1:0.25" @click.stop="setGameExpertise(2)">
            <title>knowledgeable</title>
        </circle>
        <circle cx="53" cy="7" r="5" fill="#238b45" class="exp-rating" stroke="black" :opacity="expRating == 3 ? 1:0.25" @click.stop="setGameExpertise(3)">
            <title>expert</title>
        </circle>
    </svg>
</template>

<script setup>
    import { addItemExpertise, updateItemExpertise } from '@/use/data-api';
    import { computed, onMounted, ref, watch } from 'vue';
    import { useToast } from 'vue-toastification';
    import { useTimes } from '@/store/times';
    import { useApp } from '@/store/app';
    import { storeToRefs } from 'pinia';

    const app = useApp()
    const toast = useToast()
    const times = useTimes()

    const props = defineProps({
        item: {
            type: Object,
            required: true
        },
        user: {
            type: [Number, null],
            required: true
        },
    })

    const { allowEdit } = storeToRefs(app)

    const expItem = ref(null);
    const expRating = computed(() => expItem.value ? expItem.value.value : 0);
    const userId = computed(() => props.user !== null ? props.user : 0)

    async function setGameExpertise(value) {
        if (!allowEdit.value) {
            return toast.info("editing unavailable")
        }

        if (value === expRating.value) {
            return toast.warning("already selected this value")
        }

        try {
            if (expItem.value) {
                await updateItemExpertise({
                    id: expItem.value.id,
                    item_id: props.item.id,
                    user_id: userId.value,
                    value: value
                })
            } else {
                await addItemExpertise({
                    item_id: props.item.id,
                    user_id: userId.value,
                    value: value
                })
            }
            toast.success("updated expertise for " + props.item.name)
            times.needsReload("item_expertise")
        } catch {
            toast.error("error updating expertise for " + props.item.name)
        }
    }
    function readExpertise() {
        if (props.item) {
            expItem.value = props.item.expertise.find(d => d.user_id === userId.value)
        }
    }

    onMounted(readExpertise)

    watch(() => props.item.id, readExpertise)
    watch(() => Math.max(times.all, times.item_expertise), readExpertise, { deep: true })

</script>

<style scoped>
.exp-rating:hover {
    opacity: 1;
    cursor: pointer;
}
</style>