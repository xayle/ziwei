import { ref } from 'vue'

type BirthDateParts = {
  year: number
  month: number
  day: number
  hour: number
  minute: number
}

type UseZiweiFormStateOptions = {
  birth: BirthDateParts
  gender?: string | null
  longitude?: number | null
  cityName?: string | null
  saved?: boolean
}

type FormValues = {
  year: number
  month: number
  day: number
  hour: number
  minute: number
  gender: string
  longitude?: number
}

export function useZiweiFormState(options: UseZiweiFormStateOptions) {
  const year = ref(options.birth.year)
  const month = ref(options.birth.month)
  const day = ref(options.birth.day)
  const hour = ref(options.birth.hour)
  const minute = ref(options.birth.minute)
  const gender = ref<'男' | '女'>(options.gender === 'female' ? '女' : '男')
  const liunianYear = ref<number | undefined>(undefined)
  const longitude = ref<number | undefined>(options.longitude ?? undefined)
  const initCity = ref(options.cityName || '北京')
  const showForm = ref(!options.saved)

  function setFormValues(params: FormValues) {
    year.value = params.year
    month.value = params.month
    day.value = params.day
    hour.value = params.hour
    minute.value = params.minute
    gender.value = params.gender as '男' | '女'
    longitude.value = params.longitude
  }

  return {
    year,
    month,
    day,
    hour,
    minute,
    gender,
    liunianYear,
    longitude,
    initCity,
    showForm,
    setFormValues,
  }
}
