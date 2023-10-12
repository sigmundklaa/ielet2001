
#ifndef DATA_HH__
#define DATA_HH__

#include <cstddef>
#include <cstdint>
#include <data.pb.h>
#include <pb.h>
#include <pb_encode.h>

namespace data
{
template <typename T>
std::size_t encode(const T &data, std::uint8_t *buf, std::size_t size);

template <>
std::size_t encode<sensor_data>(const sensor_data &data, std::uint8_t *buf,
                                std::size_t size)
{
    ::pb_ostream_t stream = ::pb_ostream_from_buffer(buf, size);

    return ::pb_encode(&stream, sensor_data_fields, &data);
}
}; // namespace data

#endif /* DATA_HH__ */